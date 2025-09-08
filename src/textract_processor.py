import boto3

textract = boto3.client("textract")

def extract_expense_text(bucket: str, key: str) -> str:
    print(f"📄 Rodando Textract no arquivo: s3://{bucket}/{key}")

    try:
        resp = textract.analyze_expense(
            Document={"S3Object": {"Bucket": bucket, "Name": key}}
        )

        texto_encontrado = []

        for doc in resp.get("ExpenseDocuments", []):
            for field in doc.get("Fields", []):
                field_type = field.get("Type", {}).get("Text")
                value_detection = field.get("ValueDetection")
                field_value = value_detection.get("Text") if value_detection else None

                if field_type or field_value:
                    texto_encontrado.append(f"{field_type}: {field_value}")

        texto_completo = "\n".join(texto_encontrado)

        if not texto_completo:
            raise ValueError("Nenhum texto extraído pelo Textract")

        print("✅ Extração de texto realizada")
        return texto_completo

    except Exception as e:
        print(f"❌ Erro ao processar com Textract: {e}")
        return ""
