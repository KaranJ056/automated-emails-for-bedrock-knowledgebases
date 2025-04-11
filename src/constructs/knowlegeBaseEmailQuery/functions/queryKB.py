import email
import json
import os

import boto3


def handler(event, context):
    print("request: {}".format(json.dumps(event)))

    # get environment variables
    knowledge_base_id = os.environ.get("KNOWLEDGE_BASE_ID")
    model_arn = os.environ.get("MODEL_ARN")

    # parse MIME email text for subject, body
    message = email.message_from_string(event["Payload"]["email"])
    email_body = ""
    if message.is_multipart():
        for part in message.walk():
            # each part is a either non-multipart, or another multipart message
            # that contains further parts... Message is organized like a tree
            if part.get_content_type() == "text/plain":
                email_body = part.get_payload(decode=True).decode()
    else:
        email_body = message.get_payload(decode=True).decode()

    # adjust prompt based on email body
    prompt = f"""
    You are an intelligent and friendly HR Assistant. You are helping respond to employee emails using verified HR knowledge.
 
    If the information is available in the context, include it in your response. If the information is not available, do not make up any information. Just reply with 'NO_RESPONSE'.

    NOTE: If the retrieval information is not relevant to the question asked just say "NO_RESPONSE".

    Employee Email: 
    {email_body}"""

    # call Bedrock Knowledge base with RetrieveAndGenerate
    bedrock = boto3.client("bedrock-agent-runtime")
    response_generated = True
    try:
        response = bedrock.retrieve_and_generate(
            input={"text": prompt[:1000]},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": knowledge_base_id,
                    "modelArn": model_arn,
                },
            },
            
        )
    except Exception as e:
        response_generated = False
        print(f"Exception: {e}")

    if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        response_generated = False
    
    if response["output"]["text"] == "NO_RESPONSE":
        response_generated = False

    print(f"status code= {response['ResponseMetadata']['HTTPStatusCode']}")
    print(f"response_generated= {response_generated}")
    print(response["output"]["text"])

    return {
        "email_id": event["Payload"]["email_id"],
        "response_generated": response_generated,
        "email": event["Payload"]["email"],
        "response": response["output"]["text"],
    }
