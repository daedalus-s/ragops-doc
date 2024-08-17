import json
import os
import logging
import boto3
from pinecone import Pinecone, ServerlessSpec
import voyageai
import anthropic

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize clients
pinecone_client = Pinecone(api_key=os.environ['PINECONE_API_KEY'])
vo = voyageai.Client(api_key=os.environ['VOYAGE_API_KEY'])
claude = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
s3 = boto3.client('s3')

# Constants
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
    Output as JSON with a 'keywords' key containing an array of strings."""
    response = claude.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )
    
    print(f"Raw Claude response: {response.content[0].text}")  # Debug print
    
    try:
        keywords_json = json.loads(response.content[0].text)
        return keywords_json['keywords']
    except json.JSONDecodeError:
        logging.error("Failed to parse keyword JSON")
        return []

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
        print(f"Received event: {event}")  # Debug print
        
        # Parse the input
        if 'body' in event:
            body = json.loads(event['body'])
        elif isinstance(event, dict):
            body = event
        else:
            raise ValueError("Unexpected event structure")

        print(f"Parsed body: {body}")  # Debug print

        question = body.get('question')
        
        if not question:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No question provided'})
            }
        
        print(f"Received question: {question}")  # Debug print
        
        # Generate keywords
        keywords = generate_keywords(question)
        print(f"Generated keywords: {keywords}")  # Debug print
        
        # Search for relevant products
        results = search_products(keywords)
        print(f"Found {len(results)} relevant products")  # Debug print
        
        # Generate answer
        answer = generate_answer(results, question)
        
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
        logging.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'An internal error occurred'})
        }

#Uncomment and use this function if you need to update the index with new data
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