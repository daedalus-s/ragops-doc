import json
import os
import pinecone
import voyageai
import anthropic

# Initialize clients
pinecone.init(api_key=os.environ['PINECONE_API_KEY'])
vo = voyageai.Client(api_key=os.environ['VOYAGE_API_KEY'])
claude = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

def lambda_handler(event, context):
    # Parse the incoming request
    body = json.loads(event['body'])
    question = body.get('question')
    
    if not question:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'No question provided'})
        }
    
    try:
        # Generate keywords
        keyword_prompt = f"Generate 5 diverse search keywords for: {question}. Output your response as a JSON object with a 'keywords' key containing an array of strings."
        keyword_message = claude.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=150,
            messages=[
                {"role": "user", "content": keyword_prompt}
            ]
        )
        keywords = json.loads(keyword_message.content[0].text)['keywords']
        
        # Search for relevant products
        index = pinecone.Index("amazon-products")
        results = []
        for keyword in keywords:
            query_embed = vo.embed([keyword], model="voyage-2", input_type="query").embeddings[0]
            search_results = index.query(vector=query_embed, top_k=3, include_metadata=True)
            results.extend([match['metadata']['description'] for match in search_results['matches']])
        
        # Generate answer
        answer_prompt = f"Answer this question based on the following product descriptions: {question}\n\nProducts: {results}"
        answer_message = claude.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=500,
            messages=[
                {"role": "user", "content": answer_prompt}
            ]
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'answer': answer_message.content[0].text})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }