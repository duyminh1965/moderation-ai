import json
import boto3
from boto3.dynamodb.conditions import Key
import os

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = os.environ['DYNAMODB_TABLE']

def lambda_handler(event, context):
    """
    API Gateway handler for content moderation dashboard
    """
    
    # Enable CORS
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE'
    }
    
    try:
        http_method = event['httpMethod']
        path = event['path']
        
        if http_method == 'GET' and path == '/moderation-results':
            return get_moderation_results(headers)
        elif http_method == 'GET' and path.startswith('/moderation-results/'):
            result_id = path.split('/')[-1]
            return get_moderation_result(result_id, headers)
        elif http_method == 'PUT' and path.startswith('/moderation-results/'):
            result_id = path.split('/')[-1] body =
            json.loads(event['body']) return
            update_moderation_result(result_id, body, headers)
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Not found'})
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }

def get_moderation_results(headers):
    """
    Get all moderation results
    """
    table = dynamodb.Table(TABLE_NAME)
    
    response = table.scan(
        Limit=50,
        ScanIndexForward=False
    )
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(response['Items'], default=str)
    }

def get_moderation_result(result_id, headers):
    """
    Get specific moderation result
    """
    table = dynamodb.Table(TABLE_NAME)
    
    response = table.get_item(Key={'id': result_id})
    
    if 'Item' in response:
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response['Item'], default=str)
        }
    else:
        return {
            'statusCode': 404,
            'headers': headers,
            'body': json.dumps({'error': 'Result not found'})
        }

def update_moderation_result(result_id, update_data, headers):
    """
    Update moderation result (for manual review)
    """
    table = dynamodb.Table(TABLE_NAME)
    
    # Update with manual review data
    table.update_item(
        Key={'id': result_id},
        UpdateExpression='SET manual_review = :review, review_timestamp = :timestamp',
        ExpressionAttributeValues={
            ':review': update_data,
            ':timestamp': datetime.utcnow().isoformat()
        }
    )
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({'message': 'Updated successfully'})
    }
