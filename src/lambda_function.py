import base64
import boto3
import email
import os
import uuid
import json

from gemini_processor import analisar_com_gemini
from textract_processor import extract_text

s3 = boto3.client("s3")
BUCKET_NAME = os.environ.get("BUCKET_NAME")


def lambda_handler(event, context):
    try:

        headers = {k.lower(): v for k, v in event.get("headers", {}).items()}
        content_type = headers.get("content-type")

        if not content_type or "multipart/form-data" not in content_type:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Content-Type deve ser multipart/form-data"}),
            }

        body_decodificado = base64.b64decode(event["body"])

        msg = email.message_from_bytes(
            b"Content-Type: " + content_type.encode() + b"\r\n" + body_decodificado
        )

        respostas = []
        erros = []

        for part in msg.get_payload():
            if part.get_filename(): 
                try:
                    filename = f"{uuid.uuid4()}-{part.get_filename()}"
                    file_content = part.get_payload(decode=True)

                    upload_key = f"recebidos/{filename}"
                    s3.put_object(Bucket=BUCKET_NAME, Key=upload_key, Body=file_content)
                    print(f"✅ Arquivo salvo em s3://{BUCKET_NAME}/{upload_key}")

                    texto_extraido = extract_text(BUCKET_NAME, upload_key)

                    texto_refinado = analisar_com_gemini(texto_extraido)
                    if not texto_refinado:
                        raise ValueError("Gemini não retornou resposta válida")

                    forma_pgto = (texto_refinado.get("forma_pgto") or "").lower()
                    novo_caminho = (
                        f"dinheiro/{filename}"
                        if forma_pgto in ["dinheiro", "pix"]
                        else f"outros/{filename}"
                    )

                    s3.copy_object(
                        Bucket=BUCKET_NAME,
                        CopySource={"Bucket": BUCKET_NAME, "Key": upload_key},
                        Key=novo_caminho,
                    )
                    s3.delete_object(Bucket=BUCKET_NAME, Key=upload_key)

                    texto_refinado["s3_location"] = f"s3://{BUCKET_NAME}/{novo_caminho}"

                    respostas.append(
                        {
                            "arquivo": part.get_filename(),
                            "nota_fiscal": texto_refinado,
                        }
                    )

                except Exception as e:
                    print(f"⚠️ Erro processando {part.get_filename()}: {e}")
                    erros.append({"arquivo": part.get_filename(), "erro": str(e)})

        if not respostas:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Nenhum arquivo válido encontrado", "detalhes": erros}),
            }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"status": "sucesso", "respostas": respostas, "erros": erros}, ensure_ascii=False),
        }

    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
