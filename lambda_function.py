import json
import os
import logging
import boto3
from pinecone import Pinecone, ServerlessSpec
import voyageai
import anthropic
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

pinecone_client = Pinecone(api_key=os.environ['PINECONE_API_KEY'])
vo = voyageai.Client(api_key=os.environ['VOYAGE_API_KEY'])
claude = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
s3 = boto3.client('s3')

INDEX_NAME = 'amazon-products'
DIMENSION = 1024
S3_BUCKET = os.environ['S3_BUCKET']
S3_KEY = os.environ['S3_KEY']

def ensure_index_exists():
    if INDEX_NAME not in pinecone_client.list_indexes().names():
        pinecone_client.create_index(
            name=INDEX_NAME,
            dimension=DIMENSION,
            metric='cosine',
            spec=ServerlessSpec(cloud='aws', region='us-east-1-aws')
        )
    return pinecone_client.Index(INDEX_NAME)

def clean_text(text):
    return ''.join(char for char in text if char.isprintable() or char.isspace())

def generate_keywords(question):
    prompt = f"""Generate 5 diverse search keywords for: {question}
    Output ONLY a JSON object with a 'keywords' key containing an array of strings. Do not include any explanation or additional text."""
    try:
        response = claude.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        
        raw_response = response.content[0].text
        print(f"Raw Claude response: {raw_response}") 
        
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            keywords_json = json.loads(json_str)
            return keywords_json.get('keywords', [])
        else:
            print("No JSON found in Claude's response")
            return extract_keywords(raw_response)
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        return extract_keywords(raw_response)
    except Exception as e:
        print(f"Error generating keywords: {str(e)}")
        return extract_keywords(question)

def extract_keywords(text):
    words = re.findall(r'\b\w+\b', text.lower())
    stopwords = set(['i', 'want', 'to', 'a', 'my', 'what', 'can', 'get', 'the', 'for', 'an', 'as', 'with'])
    keywords = [word for word in words if word not in stopwords and len(word) > 2]
    return list(set(keywords))[:5] 

def search_products(keywords, top_k=3):
    index = ensure_index_exists()
    results_list = []
    for keyword in keywords:
        try:
            query_embed = vo.embed([keyword], model="voyage-2", input_type="query")
            search_results = index.query(vector=query_embed.embeddings[0], top_k=top_k, include_metadata=True)
            results_list.extend([match['metadata']['description'] for match in search_results.matches])
        except Exception as e:
            logging.error(f"Error searching for keyword '{keyword}': {str(e)}")
    return results_list

def generate_answer(results, question):
    prompt = f"""Answer this question based on the following product descriptions:
    Question: {question}
    Products: {results}"""
    response = claude.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text

def lambda_handler(event, context):
    try:
        print(f"Received event: {event}") 
        

        if 'body' in event:
            body = json.loads(event['body'])
        elif isinstance(event, dict):
            body = event
        else:
            raise ValueError("Unexpected event structure")

        print(f"Parsed body: {body}") 

        question = body.get('question')
        
        if not question:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No question provided'})
            }
        
        print(f"Received question: {question}")  
        

        keywords = generate_keywords(question)
        print(f"Generated keywords: {keywords}")  


        results = search_products(keywords)
        print(f"Found {len(results)} relevant products") 
        
        if results:
            answer = generate_answer(results, question)
        else:
            answer = generate_fallback_answer(question)
        
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'question': question,
                'keywords': keywords,
                'num_results': len(results),
                'answer': answer
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'An internal error occurred'})
        }

def update_index(event, context):
     index = ensure_index_exists()
     s3_object = s3.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
     data = json.loads(s3_object['Body'].read().decode('utf-8'))
     
     to_upsert = []
     for item in data:
         text = clean_text(item['text'])
         embedding = vo.embed([text], model="voyage-2", input_type="document").embeddings[0]
         to_upsert.append((str(item['id']), embedding, {'description': text}))
         
         if len(to_upsert) == 100:
             index.upsert(vectors=to_upsert)
             to_upsert = []
     
     if to_upsert:
         index.upsert(vectors=to_upsert)
     
     return {
         'statusCode': 200,
         'body': json.dumps({'message': f'Processed {len(data)} items'})
     }