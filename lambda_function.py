import json
import boto3
import os
import base64
import uuid
from urllib.parse import parse_qs
from gemini_processor import analisar_com_gemini

s3 = boto3.client("s3")
textract = boto3.client("textract")

BUCKET_NAME = os.environ.get("BUCKET_NAME")

def lambda_handler(event, context):
    try:
        print(f"{context.aws_request_id} Iniciando processamento da nota fiscal...")

        is_base64 = event.get("isBase64Encoded", False)
        body = event.get("body", "")
        if is_base64:
            print(f"{context.aws_request_id} Requisição base64 detectada.")
            body = base64.b64decode(body)

        headers = {k.lower(): v for k, v in event.get("headers", {}).items()}
        content_type = headers.get("content-type", "")

        if "multipart/form-data" in content_type:
            print(f"{context.aws_request_id} Detectado multipart/form-data, extraindo arquivo...")
            boundary = content_type.split("boundary=")[1]
            parts = body.split(b"--" + boundary.encode())
            file_content = None
            filename = str(uuid.uuid4()) + ".jpg"

            for part in parts:
                if b"Content-Disposition" in part and b"filename=" in part:
                    file_content = part.split(b"\r\n\r\n", 1)[1].rsplit(b"\r\n", 1)[0]

            if not file_content:
                raise ValueError("Nenhum arquivo encontrado no corpo da requisição")

            s3_key = f"recebidos/{filename}"
            s3.put_object(Bucket=BUCKET_NAME, Key=s3_key, Body=file_content)
            print(f"{context.aws_request_id} 📄 Arquivo salvo em s3://{BUCKET_NAME}/{s3_key}")
        else:
            raise ValueError("Formato não suportado. Envie multipart/form-data.")

        print(f"{context.aws_request_id} Rodando Textract no arquivo: s3://{BUCKET_NAME}/{s3_key}")
        response = textract.detect_document_text(
            Document={"S3Object": {"Bucket": BUCKET_NAME, "Name": s3_key}}
        )

        extracted_text = "\n".join(
            [b["Text"] for b in response["Blocks"] if b["BlockType"] == "LINE"]
        )

        if not extracted_text.strip():
            raise ValueError("Textract não retornou texto.")

        dados_estruturados = analisar_com_gemini(extracted_text)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "mensagem": "Processamento concluído com sucesso",
                    "arquivo": s3_key,
                    "dados": dados_estruturados,
                },
                ensure_ascii=False,
            ),
        }

    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"erro": str(e)}, ensure_ascii=False),
        }
