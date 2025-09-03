import json
import os
import urllib.parse
import boto3

s3 = boto3.client('s3')
textract = boto3.client('textract')

def lambda_handler(event, context):
    s3_event = event['Records'][0]['s3']
    bucket = s3_event['bucket']['name']
    original_key = urllib.parse.unquote_plus(s3_event['object']['key'], encoding='utf-8')

    print(f'Processando arquivo: s3://{bucket}/{original_key}')

    try:
        # Chama o Textract para analisar o documento
        response = textract.analyze_expense(
            Document={'S3Object': {'Bucket': bucket, 'Name': original_key}}
        )

        # Processa a resposta do Textract para montar o texto completo
        texto_completo = ''
        for doc in response.get('ExpenseDocuments', []): # Itera sobre os documentos encontrados
            for field in doc.get('SummaryFields', []): # Itera sobre os campos de resumo
                label = field.get('LabelDetection', {}).get('Text', '')
                value = field.get('ValueDetection', {}).get('Text', '')
                texto_completo += f'{label}: {value}\n'  # Concatena o texto que foi extraído

        if not texto_completo:
            raise ValueError('❌ Textract não conseguiu extrair texto do documento.')

        print("--- Texto Extraído pelo Textract ---")
        print(texto_completo)

        # Lógica da LLM e de mover arquivos virá aqui

    except Exception as e:
        print(f'❌ Erro no processamento do arquivo {original_key}: {e}')