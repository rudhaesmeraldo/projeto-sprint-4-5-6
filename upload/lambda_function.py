import base64
import boto3
import email
import os
import uuid

s3 = boto3.client('s3')
BUCKET_NAME = os.environ.get('BUCKET_NAME') # Pega o nome do bucket das variáveis de ambiente

def lambda_handler(event, context):
    try:
        # Pega os headers do evento
        headers = event.get('params', {}).get('header', {})
        # Procura pelo content-type de forma case-insensitive
        content_type = next((headers[key] for key in headers if key.lower() == 'content-type'), None)

        if not content_type:
            raise ValueError("Header 'Content-Type' não encontrado na requisição.")

        body_decodificado = base64.b64decode(event['body-json']) # O corpo vem em 'body-json'

        # Cria uma mensagem a partir dos bytes para facilitar o parse do multipart
        msg = email.message_from_bytes(b'Content-Type: ' + content_type.encode() + b'\r\n' + body_decodificado)

        for part in msg.get_payload(): # Itera sobre as partes do formulário
            if part.get_filename(): # Verifica se a parte é um arquivo
                filename = f"{uuid.uuid4()}-{part.get_filename()}" # Cria um nome de arquivo único
                file_content = part.get_payload(decode=True) # Pega o conteúdo do arquivo

                upload_key = f'recebidos/{filename}' # Define o caminho de upload no S3

                s3.put_object( # Envia o objeto para o S3
                    Bucket=BUCKET_NAME,
                    Key=upload_key,
                    Body=file_content
                )

                print(f'✅ Arquivo salvo com sucesso em s3://{BUCKET_NAME}/{upload_key}')

                return {
                    'message': '❗Arquivo recebido e aguardando processamento.'
                }

        return {'message': '❌ Nenhum arquivo encontrado na requisição.'}
    except Exception as e:
        print(f'Erro: {e}')
        # erro do API Gateway
        raise Exception(f'❌ Erro no servidor: {e}')