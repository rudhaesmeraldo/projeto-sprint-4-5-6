import os
import boto3
import base64
import email

BUCKET_NAME = os.environ.get("BUCKET_NAME")
s3_client = boto3.client("s3")

def lambda_handler(event, context):
    try:
        headers = event.get("headers") or event.get("params", {}).get("header", {})
        content_type = next(
            (value for key, value in headers.items() if key.lower() == "content-type"),
            None
        )
        if not content_type:
            raise ValueError("Header 'Content-Type' não encontrado.")

        raw_body = base64.b64decode(event["body"])
        msg = email.message_from_bytes(b"Content-Type: " + content_type.encode() + b"\r\n" + raw_body)

        for part in msg.get_payload():
            filename = part.get_filename()
            if filename:
                file_content = part.get_payload(decode=True)
                s3_client.put_object(Bucket=BUCKET_NAME, Key=filename, Body=file_content)
                return {"statusCode": 200, "body": f"Arquivo {filename} salvo com sucesso no bucket {BUCKET_NAME}"}

        return {"statusCode": 400, "body": "Nenhum arquivo encontrado no multipart."}

    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
