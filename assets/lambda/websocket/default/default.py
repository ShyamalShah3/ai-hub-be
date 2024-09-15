import boto3
import json
import os

def lambda_handler(event, context):
    print("Event:", event)

    # Extract connection details
    connection_id = event['requestContext']['connectionId']
    domain_name = event['requestContext']['domainName']
    stage = event['requestContext']['stage']
    endpoint_url = f"https://{domain_name}/{stage}"

    print("Connection ID:", connection_id)
    print("Endpoint URL:", endpoint_url)

    # Initialize the API Gateway management client
    apigw_client = boto3.client('apigatewaymanagementapi', endpoint_url=endpoint_url)

    message = {
        'message': 'Use the chat route to send a message. Your info:',
        'connectionId': connection_id,
        'requestId': event['requestContext']['requestId'],
    }

    # Send the message back to the client
    try:
        apigw_client.post_to_connection(
            Data=json.dumps(message).encode('utf-8'),
            ConnectionId=connection_id
        )
    except apigw_client.exceptions.GoneException:
        # Handle the case where the connection is no longer available
        print(f"Connection {connection_id} is gone.")
    except Exception as e:
        print(f"Error sending message: {e}")

    return {
        'statusCode': 200,
        'body': 'Message sent.'
    }