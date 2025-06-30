import json
import boto3
import os
from datetime import datetime
import uuid

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
rekognition = boto3.client('rekognition')
bedrock = boto3.client('bedrock-runtime')
sns = boto3.client('sns')

# Environment variables
TABLE_NAME = os.environ['DYNAMODB_TABLE']
SNS_TOPIC = os.environ['SNS_TOPIC_ARN']

def lambda_handler(event, context):
    """
    Main Lambda function triggered by S3 upload
    """
    try:
        # Parse S3 event
        for record in event['Records']:
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            # Process the uploaded content
            result = process_content(bucket, key)
            
            # Store results in DynamoDB
            store_moderation_result(result)
            
            # Send notification if inappropriate content detected
            if result['is_inappropriate']:
                send_notification(result)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Content processed successfully')
        }
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing content: {str(e)}')
        }

def process_content(bucket, key):
    """
    Analyze content using AWS AI services
    """
    # Get file metadata
    response = s3.head_object(Bucket=bucket, Key=key)
    content_type = response['ContentType']
    file_size = response['ContentLength']
    
    result = {
        'id': str(uuid.uuid4()),
        'bucket': bucket,
        'key': key,
        'content_type': content_type,
        'file_size': file_size,
        'timestamp': datetime.utcnow().isoformat(),
        'moderation_results': {},
        'is_inappropriate': False,
        'confidence_score': 0
    }
    
    # Process based on content type
    if content_type.startswith('image/'):
        result['moderation_results'] = analyze_image(bucket, key)
    elif content_type.startswith('video/'):
        result['moderation_results'] = analyze_video(bucket, key)
    elif content_type.startswith('text/'):
        result['moderation_results'] = analyze_text(bucket, key)
    
    # Determine if content is inappropriate
    result['is_inappropriate'] = is_content_inappropriate(result['moderation_results'])
    result['confidence_score'] = calculate_confidence(result['moderation_results'])
    
    return result

def analyze_image(bucket, key):
    """
    Use Rekognition to analyze images
    """
    try:
        response = rekognition.detect_moderation_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            MinConfidence=60
        )
        
        return {
            'service': 'rekognition',
            'labels': response['ModerationLabels'],
            'detected_inappropriate': len(response['ModerationLabels']) > 0
        }
    except Exception as e:
        print(f"Rekognition error: {str(e)}")
        return {'service': 'rekognition', 'error': str(e)}

def analyze_video(bucket, key):
    """
    Use Rekognition to analyze videos
    """
    try:
        # Start video moderation job
        response = rekognition.start_content_moderation(
            Video={'S3Object': {'Bucket': bucket, 'Name': key}},
            MinConfidence=60
        )
        
        job_id = response['JobId']
        
        # Note: In production, you'd use another Lambda to poll for results
        # For this demo, we'll return the job ID
        return {
            'service': 'rekognition_video',
            'job_id': job_id,
            'status': 'processing'
        }
    except Exception as e:
        print(f"Rekognition video error: {str(e)}")
        return {'service': 'rekognition_video', 'error': str(e)}

def analyze_text(bucket, key):
    """
    Use Bedrock to analyze text content
    """
    try:
        # Download text content
        obj = s3.get_object(Bucket=bucket, Key=key)
        text_content = obj['Body'].read().decode('utf-8')
        
        # Prepare Bedrock request
        prompt = f"""
        Analyze the following text for inappropriate content including:
        - Hate speech
        - Violence or threats
        - Adult content
        - Harassment or bullying
        - Spam or misleading information
        
        Text to analyze: "{text_content}"
        
        Respond with JSON format:
        {{
            "is_inappropriate": true/false,
            "categories": ["category1", "category2"],
            "confidence": 0.0-1.0,
            "reasoning": "explanation"
        }}
        """
        
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1000,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        content = result['content'][0]['text']
        
        return {
            'service': 'bedrock',
            'analysis': json.loads(content),
            'detected_inappropriate': json.loads(content).get('is_inappropriate', False)
        }
        
    except Exception as e:
        print(f"Bedrock error: {str(e)}")
        return {'service': 'bedrock', 'error': str(e)}

def is_content_inappropriate(moderation_results):
    """
    Determine if content is inappropriate based on analysis
    """
    if 'error' in moderation_results:
        return False
    
    return moderation_results.get('detected_inappropriate', False)

def calculate_confidence(moderation_results):
    """
    Calculate overall confidence score
    """
    if 'error' in moderation_results:
        return 0
    
    if moderation_results['service'] == 'rekognition':
        labels = moderation_results.get('labels', [])
        if labels:
            return max([label['Confidence'] for label in labels]) / 100
    elif moderation_results['service'] == 'bedrock':
        analysis = moderation_results.get('analysis', {})
        return analysis.get('confidence', 0)
    
    return 0

def store_moderation_result(result):
    """
    Store moderation results in DynamoDB
    """
    table = dynamodb.Table(TABLE_NAME)
    
    table.put_item(Item=result)

def send_notification(result):
    """
    Send SNS notification for inappropriate content
    """
    message = {
        'alert': 'Inappropriate content detected',
        'file': f"s3://{result['bucket']}/{result['key']}",
        'confidence': result['confidence_score'],
        'timestamp': result['timestamp']
    }
    
    sns.publish(
        TopicArn=SNS_TOPIC,
        Message=json.dumps(message),
        Subject='Content Moderation Alert'
    )