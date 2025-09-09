import boto3

textract = boto3.client("textract")

def processar_com_textract(bucket: str, key: str) -> str:
    print(f"📄 Rodando Textract no arquivo: s3://{bucket}/{key}")

    try:
        if key.lower().endswith(".pdf"):
            resp = textract.analyze_expense(
                Document={"S3Object": {"Bucket": bucket, "Name": key}}
            )

            texto_encontrado = []
            for doc in resp.get("ExpenseDocuments", []):
                for field in doc.get("SummaryFields", []):
                    label = field.get("LabelDetection", {}).get("Text", "")
                    value = field.get("ValueDetection", {}).get("Text", "")
                    
                    if label:
                        texto_encontrado.append(label)
                    if value:
                        texto_encontrado.append(value)
            
            texto_completo = "\n".join(texto_encontrado)

        else:
            resp = textract.detect_document_text(
                Document={"S3Object": {"Bucket": bucket, "Name": key}}
            )

            texto_encontrado = []
            for item in resp.get("Blocks", []):
                if item["BlockType"] == "LINE":
                    texto_encontrado.append(item["Text"])

            texto_completo = "\n".join(texto_encontrado)

        if not texto_completo:
            raise ValueError("Nenhum texto extraído pelo Textract")

        print("✅ Extração de texto realizada")
        return texto_completo

    except Exception as e:
        print(f"❌ Erro ao processar com Textract: {e}")
        return ""
