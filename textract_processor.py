import boto3
import json

textract = boto3.client("textract")

def extract_text(bucket: str, key: str) -> str:
    print(f"📄 Rodando Textract no arquivo: s3://{bucket}/{key}")

    resp = textract.analyze_expense(
        Document={"S3Object": {"Bucket": bucket, "Name": key}}
    )

    resultado = {}

    for doc in resp.get("ExpenseDocuments", []):
        for field in doc.get("SummaryFields", []):
            label = field.get("LabelDetection", {}).get("Text", "").strip()
            value = field.get("ValueDetection", {}).get("Text", "").strip()
            if label and value:
                chave = label.replace(" ", "_").replace(":", "")
                resultado[chave] = value

    if not resultado:
        raise ValueError("❌ Nenhum texto extraído pelo Textract.")

    print("✅ Extração concluída com sucesso.")
    return json.dumps(resultado, ensure_ascii=False, indent=2)
