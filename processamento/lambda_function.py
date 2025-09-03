import json
import urllib.parse

def lambda_handler(event, context):
    s3_event = event['Records'][0]['s3']
    bucket = s3_event['bucket']['name']
    original_key = urllib.parse.unquote_plus(s3_event['object']['key'], encoding='utf-8')

    print(f'Processando arquivo: s3://{bucket}/{original_key}')

    try:
        print("Estrutura básica da função de processamento criada com sucesso.")

    except Exception as e:
        print(f'❌ Erro no processamento do arquivo {original_key}: {e}')

    return {
        'statusCode': 200,
        'body': json.dumps('Processamento concluído.')
    }