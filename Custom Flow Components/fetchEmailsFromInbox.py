import imaplib
import email
from email.header import decode_header
import os
from dotenv import load_dotenv
import uuid
import boto3
import time

load_dotenv()

def lambda_handler(event, context):

    # Connect to Gmail's IMAP server
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(os.getenv("EMAIL"), os.getenv("PASSWORD"))

    # Select the inbox and search for unread messages
    imap.select("inbox")
    status, messages = imap.search(None, 'UNSEEN')  # Use 'ALL' to get all messages

    email_ids = messages[0].split()

    unseen_emails = []
    for email_id in email_ids:
        res, msg_data = imap.fetch(email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or "utf-8")
                from_ = msg.get("From")
                date = msg.get("Date")
                body = ""

                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))

                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()

                unseen_emails.append({
                    "from": from_,
                    "subject": subject,
                    "timestamp": date,
                    "body": body
                })

    imap.logout()

    s3 = boto3.client('s3')

    bucket_name = os.environ.get('S3_BUCKET_NAME')
    
    if not bucket_name:
        return {
            'statusCode': 400,
            'body': 'S3 bucket name does not provided.'
        }

    for unseen_email in unseen_emails:
        from_address = unseen_email['from'].split('<')[-1].split('>')[0]
        subject = unseen_email['subject']
        email_body = unseen_email['body']
        timestamp = unseen_email['timestamp']

        # Format the email content
        formatted_email = (
            f"FROM: {from_address}\n"
            f"SUBJECT: {subject}\n"
            f"DATE: {timestamp}\n"
            f"BODY:\n{email_body}"
        )

        # Generate a unique file name for the email
        file_name = f"emails/{uuid.uuid4()}-{from_address}"

        try:
            # Upload the formatted email content to the S3 bucket
            s3.put_object(
                Bucket=bucket_name,
                Key=file_name,
                Body=formatted_email,
                ContentType='text/plain'
            )
            
            print(f"Email from {from_address} stored in S3 as {file_name}")
        except Exception as e:
            return {
                'statusCode': 500,
                'body': f"Failed to store email: \n{str(e)}."
            }

    return {
        'statusCode': 200,
        'body': f"Email stored successfully in {bucket_name}/{file_name}."
    }

if __name__ == "__main__":
    print(lambda_handler(None, None))