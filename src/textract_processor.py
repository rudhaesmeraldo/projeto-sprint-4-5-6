import boto3
import json

textract = boto3.client("textract")

def extract_text(bucket: str, key: str) -> str:
    print(f"📄 Rodando Textract no arquivo: s3://{bucket}/{key}")

    resp = textract.analyze_expense(
        Document={"S3Object": {"Bucket": bucket, "Name": key}}
    )

    print("✅ Extração concluída com sucesso.")
    return json.dumps(resp, ensure_ascii=False, indent=2)
