import boto3
import json
import os
import urllib.parse
import urllib.request

s3 = boto3.client('s3')
textract = boto3.client('textract')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

def extrair_dados_com_llm(texto_extraido): # chama a API do Gemini
    print('❗Iniciando extração de dados com a API do Gemini...')

    # url da API
    url = f'[https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=](https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=){GEMINI_API_KEY}'

    # Prompt do Gemini
    prompt = f"""
    Analise o seguinte texto extraído de uma nota fiscal e retorne APENAS um objeto JSON válido com os seguintes campos: "nome_emissor", "CNPJ_emissor", "endereco_emissor", "CNPJ_CPF_consumidor", "data_emissao", "numero_nota_fiscal", "serie_nota_fiscal", "valor_total", "forma_pgto".

    Siga estas regras estritamente:
    - O CNPJ deve estar no formato XX.XXX.XXX/XXXX-XX. Se encontrar um CPF, formate como XXX.XXX.XXX-XX.
    - A data_emissao deve estar no formato DD/MM/AAAA.
    - O valor_total deve ser uma string contendo apenas números e um ponto como separador decimal (ex: "123.45").
    - A forma_pgto deve ser uma das seguintes strings: "dinheiro", "pix", "cartao", ou "outros".
    - Se um campo não for encontrado no texto, o valor correspondente no JSON deve ser null (o valor nulo do JSON, não a string "None").
    - Não inclua ```json e ``` no início ou fim da sua resposta.
    - Não inclua nenhuma explicação ou texto adicional na sua resposta, apenas o objeto JSON.

    Texto da nota fiscal:
    ---
    {texto_extraido}
    ---
    """

    # requisição para a API
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    # Converte o dicionário para bytes JSON
    json_data = json.dumps(data).encode('utf-8')

    # Cria a requisição
    req = urllib.request.Request(url, data=json_data, headers={'Content-Type': 'application/json'})

    try:
        with urllib.request.urlopen(req) as response:
            response_body = json.loads(response.read())

            # Extrai o texto da resposta
            json_response_text = response_body['candidates'][0]['content']['parts'][0]['text']

            print("--- Resposta da LLM ---")
            print(json_response_text)

            # Converte a string de resposta em um dicionário
            return json.loads(json_response_text)

    except Exception as e:
        print(f"❌ Erro ao chamar a API do Gemini: {e}")
        # Detalha o erro
        if hasattr(e, 'read'):
            print(f"Detalhes do erro: {e.read().decode()}")
        return None


def lambda_handler(event, context):
    s3_event = event['Records'][0]['s3']
    bucket = s3_event['bucket']['name']
    original_key = urllib.parse.unquote_plus(s3_event['object']['key'], encoding='utf-8')
    nome_arquivo = original_key.split('/')[-1]

    print(f'Processando arquivo: s3://{bucket}/{original_key}')
    try:
        # Chama o Textract
        response = textract.analyze_expense(Document={'S3Object': {'Bucket': bucket, 'Name': original_key}})

        texto_completo = ''
        for doc in response.get('ExpenseDocuments', []): # Itera sobre os documentos encontrados
            for field in doc.get('SummaryFields', []): # Itera sobre os campos de resumo
                label = field.get('LabelDetection', {}).get('Text', '')
                value = field.get('ValueDetection', {}).get('Text', '')
                texto_completo += f'{label}: {value}\n'  # Concatena o texto que foi extraído

        if not texto_completo:
            raise ValueError('❌ Textract não conseguiu extrair texto do documento.')

        dados_finais = extrair_dados_com_llm(texto_completo) # Envia o texto para a LLM
        if not dados_finais:
            raise ValueError('❌ Falha ao processar dados com a LLM.')

        print('--- JSON Final ---\n' + json.dumps(dados_finais, indent=2))

        forma_pgto = dados_finais.get('forma_pgto', 'outros').lower() # Pega a forma de pagamento
        nova_chave = f'processados/{forma_pgto}/{nome_arquivo}' # Define a pasta de destino

    except Exception as e:
        print(f'❌ Erro no processamento do arquivo {original_key}: {e}')
        nova_chave = f'falhas/{nome_arquivo}' # Define a pasta de destino de falha

    # Move o arquivo para o destino final (deu bom ou deu ruim)
    s3.copy_object(Bucket=bucket, CopySource={'Bucket': bucket, 'Key': original_key}, Key=nova_chave)
    s3.delete_object(Bucket=bucket, Key=original_key)
    print(f'✅ Arquivo movido para: s3://{bucket}/{nova_chave}')