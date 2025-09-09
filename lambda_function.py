import json
import base64
import boto3
import uuid
import os
import unicodedata

from textract_processor import processar_com_textract
from gemini_processor import analisar_com_gemini

s3 = boto3.client('s3')
BUCKET_NAME = "bucket-projeto-squad-6"

def remover_acentos(texto: str) -> str:
    # A sua função de remover acentos já está correta, mas vou mantê-la como referência.
    # No seu caso, o problema não é com o texto do Gemini, mas com o corpo da requisição.
    pass

def lambda_handler(event, context):
    print("Iniciando processamento da nota fiscal...")
    print("teste123")
    
    # 1. Obter o corpo da requisição e remover caracteres inválidos
    try:
        # A API Gateway pode enviar o corpo como uma string ou um Base64.
        # Vamos tentar decodificar o Base64.
        if event.get('isBase64Encoded', False):
            # Se for Base64, apenas decodifique. O problema pode ser na string
            # que a API Gateway gerou, não na sua decodificação.
            # Se for uma string comum, essa linha pode falhar.
            file_content = base64.b64decode(event['body'])
        else:
            # Se não for Base64, pode ser texto puro.
            # O ideal é que o cliente envie sempre em Base64.
            # Se o erro persiste na decodificação, vamos "limpar" a string
            # antes de decodificar para tentar remover caracteres estranhos.
            body_string = event['body']
            # Esta limpeza pode não funcionar se a string já estiver corrompida.
            # Mas é uma tentativa para contornar o problema.
            body_string_limpa = unicodedata.normalize('NFKC', body_string).encode('ascii', 'ignore').decode('ascii')
            file_content = base64.b64decode(body_string_limpa)
            
    except Exception as e:
        print(f"ERRO ao decodificar a imagem: {str(e)}")
        # Se a decodificação falhar, retorne um erro amigável ao cliente.
        return {'statusCode': 400, 'body': json.dumps({'erro': f'Erro na decodificação do corpo da requisição: {str(e)}'})}
    
    # O restante do seu código pode ser movido para este ponto
    filename = f"{uuid.uuid4()}.png"
    s3_key_recebido = f"recebidos/{filename}"

    try:
       
        print(f"Salvando arquivo em s3://{BUCKET_NAME}/{s3_key_recebido}")
        s3.put_object(Bucket=BUCKET_NAME, Key=s3_key_recebido, Body=file_content)
        print("colocado em", s3_key_recebido)
        
        texto_extraido = processar_com_textract(BUCKET_NAME, s3_key_recebido)
        if not texto_extraido:
            raise ValueError("Textract não retornou texto.")

        dados_finais = analisar_com_gemini(texto_extraido)
        if not dados_finais:
            raise ValueError("Gemini não retornou dados válidos.")

        forma_pgto = dados_finais.get('forma_pgto', 'outros').lower()
        pasta_destino = "dinheiro" if forma_pgto in ["dinheiro", "pix"] else "outros"
        s3_key_destino = f"processados/{pasta_destino}/{filename}"

        print(f"Movendo arquivo para s3://{BUCKET_NAME}/{s3_key_destino}")
        s3.copy_object(Bucket=BUCKET_NAME, CopySource={'Bucket': BUCKET_NAME, 'Key': s3_key_recebido}, Key=s3_key_destino)
        s3.delete_object(Bucket=BUCKET_NAME, Key=s3_key_recebido)

        print("Processamento concluído com sucesso!")
        return {'statusCode': 200, 'body': json.dumps(dados_finais, ensure_ascii=False)}

    except Exception as e:
        print(f"ERRO GERAL: {str(e)}")
        # ... seu código para mover para a pasta de falhas ...
        try:
            s3_key_falha = f"falhas/{filename}"
            print(f"Movendo arquivo para a pasta de falhas: s3://{BUCKET_NAME}/{s3_key_falha}")
            s3.copy_object(Bucket=BUCKET_NAME, CopySource={'Bucket': BUCKET_NAME, 'Key': s3_key_recebido}, Key=s3_key_falha)
            s3.delete_object(Bucket=BUCKET_NAME, Key=s3_key_recebido)
        except Exception as move_error:
            print(f"ERRO adicional ao tentar mover para falhas: {move_error}")

        return {'statusCode': 500, 'body': json.dumps({'erro': f'Erro interno: {str(e)}'}, ensure_ascii=False)}