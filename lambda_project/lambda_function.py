import json
import os
import boto3
import pinecone
import voyageai
import anthropic
import time
import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
# Initialize clients
s3 = boto3.client('s3')
pinecone.init(api_key=os.environ['PINECONE_API_KEY'])
vo = voyageai.Client(api_key=os.environ['VOYAGE_API_KEY'])
claude = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
index = pinecone.Index("amazon-products")

DATA_BUCKET = 'ragops-data'
DATA_KEY = 'amazon-products.jsonl'

def lambda_handler(event, context):
    install('async_timeout')
    install('aiohttp')
    import async_timeout
    import aiohttp
    try:
        # Parse the incoming request
        body = json.loads(event['body'])
        question = body.get('question')
        
        if not question:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No question provided'})
            }
        
        # Process flow
        process_log = []
        
        # Step 1: Load sample data
        process_log.append("Step 1: Loading sample data from S3")
        sample_data = load_sample_data_from_s3()
        process_log.append(f"Loaded {len(sample_data)} sample products")
        
        # Step 2: Create embeddings
        process_log.append("Step 2: Creating embeddings with VoyageAI")
        embeddings = create_embeddings(sample_data)
        process_log.append(f"Created {len(embeddings)} embeddings")
        
        # Step 3: Upsert to Pinecone
        process_log.append("Step 3: Upserting embeddings to Pinecone")
        upsert_to_pinecone(sample_data, embeddings)
        process_log.append("Upserted embeddings to Pinecone")
        
        # Step 4: Generate keywords
        process_log.append("Step 4: Generating keywords for the question")
        keywords = generate_keywords(question)
        process_log.append(f"Generated keywords: {keywords}")
        
        # Step 5: Search for relevant products
        process_log.append("Step 5: Searching for relevant products")
        results = search_products(keywords)
        process_log.append(f"Found {len(results)} relevant products")
        
        # Step 6: Generate answer
        process_log.append("Step 6: Generating answer")
        answer = generate_answer(results, question)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'process_log': process_log,
                'answer': answer
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def load_sample_data_from_s3():
    response = s3.get_object(Bucket=DATA_BUCKET, Key=DATA_KEY)
    content = response['Body'].read().decode('utf-8')
    lines = content.split('\n')[:10]  # Load just 10 samples for demonstration
    return [json.loads(line) for line in lines if line.strip()]

def create_embeddings(data):
    texts = [item['text'] for item in data]
    embeddings = vo.embed(texts, model="voyage-2", input_type="document")
    return embeddings.embeddings

def upsert_to_pinecone(data, embeddings):
    to_upsert = [
        (f"product_{i}", embedding, {"description": item['text']})
        for i, (item, embedding) in enumerate(zip(data, embeddings))
    ]
    index.upsert(vectors=to_upsert)

def generate_keywords(question):
    prompt = f"""Generate 5 diverse search keywords for: {question}
    Output as JSON with a 'keywords' key containing an array of strings."""
    response = claude.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}]
    )
    keywords = json.loads(response.content[0].text)['keywords']
    return keywords

def search_products(keywords, top_k=3):
    results = []
    for keyword in keywords:
        query_embed = vo.embed([keyword], model="voyage-2", input_type="query").embeddings[0]
        search_results = index.query(vector=query_embed, top_k=top_k, include_metadata=True)
        results.extend([match['metadata']['description'] for match in search_results['matches']])
    return results

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