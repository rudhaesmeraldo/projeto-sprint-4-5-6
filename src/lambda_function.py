import base64
import boto3
import os
import uuid
import json
from io import BytesIO
from multipart import MultipartParser

from gemini_processor import analisar_com_gemini
from textract_processor import extract_text

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME')


def lambda_handler(event, context):
    try:
        body_bytes = base64.b64decode(event['body'])
        headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
        content_type = headers.get('content-type')

        if not content_type or 'multipart/form-data' not in content_type:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Content-Type deve ser multipart/form-data"})
            }

        parser = MultipartParser(BytesIO(body_bytes), content_type)
        respostas = []
        erros = []

        for part in parser.parts():
            filename = part.filename
            if filename:
                try:
                    file_content = part.raw
                    upload_key = f"recebidos/{uuid.uuid4()}-{filename}"

                    s3.put_object(Bucket=BUCKET_NAME, Key=upload_key, Body=file_content)
                    print(f"✅ Arquivo salvo em s3://{BUCKET_NAME}/{upload_key}")

                    texto_extraido = extract_text(BUCKET_NAME, upload_key)

    
                    texto_refinado = analisar_com_gemini(texto_extraido)
                    if not texto_refinado:
                        raise ValueError("Gemini não retornou texto válido")

                    forma_pgto = (texto_refinado.get("forma_pgto") or "").lower()
                    novo_caminho = f"dinheiro/{filename}" if forma_pgto in ["dinheiro", "pix"] else f"outros/{filename}"

                    s3.copy_object(
                        Bucket=BUCKET_NAME,
                        CopySource={'Bucket': BUCKET_NAME, 'Key': upload_key},
                        Key=novo_caminho
                    )
                    s3.delete_object(Bucket=BUCKET_NAME, Key=upload_key)
                    texto_refinado["s3_location"] = f"s3://{BUCKET_NAME}/{novo_caminho}"

                    respostas.append({
                        "arquivo": filename,
                        "nota_fiscal": texto_refinado
                    })

                except Exception as e:
                    print(f"⚠️ Erro processando {filename}: {e}")
                    erros.append({"arquivo": filename, "erro": str(e)})

        if not respostas:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Nenhum arquivo processado", "detalhes": erros})
            }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"status": "sucesso", "respostas": respostas, "erros": erros}, ensure_ascii=False)
        }

    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
