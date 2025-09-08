import base64
import boto3
import email
import os
import uuid
import json

from textract_processor import extract_text
from gemini_processor import analisar_com_gemini

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME') 

def lambda_handler(event, context):
    try:
        headers = event.get('params', {}).get('header', {})
        content_type = next((headers[key] for key in headers if key.lower() == 'content-type'), None)

        if not content_type:
            raise ValueError("Header 'Content-Type' não encontrado na requisição.")

        body_decodificado = base64.b64decode(event['body-json'])
        msg = email.message_from_bytes(b'Content-Type: ' + content_type.encode() + b'\r\n' + body_decodificado)

        respostas = []

        for part in msg.get_payload(): 
            if part.get_filename(): 
                filename = f"{uuid.uuid4()}-{part.get_filename()}"  
                file_content = part.get_payload(decode=True)

                upload_key = f'recebidos/{filename}'

                s3.put_object(
                    Bucket=BUCKET_NAME,
                    Key=upload_key,
                    Body=file_content
                )
                print(f'✅ Arquivo salvo com sucesso em s3://{BUCKET_NAME}/{upload_key}')

                texto_extraido = extract_text(BUCKET_NAME, upload_key)

                nota_fiscal = analisar_com_gemini(texto_extraido)
                if not nota_fiscal:
                    raise ValueError("Gemini não retornou dados válidos da nota.")

                forma_pgto = (nota_fiscal.get("forma_pgto") or "").lower()
                pasta_final = "dinheiro" if forma_pgto in ["dinheiro", "pix"] else "outros"
                novo_caminho = f"{pasta_final}/{filename}"

                s3.copy_object(
                    Bucket=BUCKET_NAME,
                    CopySource={"Bucket": BUCKET_NAME, "Key": upload_key},
                    Key=novo_caminho
                )
                s3.delete_object(Bucket=BUCKET_NAME, Key=upload_key)

                nota_fiscal['s3_location'] = f's3://{BUCKET_NAME}/{novo_caminho}'

                respostas.append({
                    "arquivo": part.get_filename(),
                    "nota_fiscal": nota_fiscal
                })

        if not respostas:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Nenhum arquivo encontrado na requisição"})
            }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"status": "sucesso", "respostas": respostas}, ensure_ascii=False)
        }

    except Exception as e:
        print(f'❌ Erro: {e}')
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
