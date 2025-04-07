import boto3
import os
import uuid
import json
 
s3 = boto3.client('s3')
 
def lambda_handler(event, context):
    # Parse the email content from the Google Apps Script payload
    try:
        body = json.loads(event['body'])  # Extract the body from the HTTP request
        email_content = body.get('email_content', {})
        to_address = email_content.get('to', '')
        from_address = email_content.get('from', '')
        subject = email_content.get('subject', '')
        timestamp = email_content.get('timestamp', '')
        email_body = email_content.get('body', '')
    except (KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'body': 'Invalid request payload or missing email content.'
        }
   
    # Get the S3 bucket name from environment variables
    bucket_name = os.environ.get('S3_BUCKET_NAME')
   
    if not bucket_name or not email_content:
        return {
            'statusCode': 400,
            'body': 'Missing email content or S3 bucket name.'
        }
   
    # Format the email content
    formatted_email = (
        f"TO: {to_address}\n"
        f"FROM: {from_address}\n"
        f"SUBJECT: {subject}\n"
        f"TIMESTAMP: {timestamp}\n"
        f"BODY:\n{email_body}"
    )
   
    # Generate a unique file name for the email
    file_name = f"emails/{uuid.uuid4()}-{to_address}"
   
    try:
        # Upload the formatted email content to the S3 bucket
        s3.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=formatted_email,
            ContentType='text/plain'
        )
        return {
            'statusCode': 200,
            'body': f"Email stored successfully in {bucket_name}/{file_name}"
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Failed to store email: {str(e)}"
        }