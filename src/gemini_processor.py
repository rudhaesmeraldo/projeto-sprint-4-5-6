import json
import os
import urllib.request

# Obtém a chave da API das variáveis de ambiente
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

def analisar_com_gemini(texto_extraido: str) -> dict: # chama a API do Gemini
    print('❗Iniciando extração de dados com a API do Gemini...')

    # url da API
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}'

    # Prompt do Gemini
    prompt = f"""
    Analise o seguinte texto extraído de uma nota fiscal e retorne APENAS um objeto JSON válido com os seguintes campos: "nome_emissor", "CNPJ_emissor", "endereco_emissor", "CNPJ_CPF_consumidor", "data_emissao", "numero_nota_fiscal", "serie_nota_fiscal", "valor_total", "forma_pgto".

    Siga estas regras estritamente:
    - O CNPJ deve estar no formato XX.XXX.XXX/XXXX-XX. Se encontrar um CPF, formate como XXX.XXX.XXX-XX.
    - A data_emissao deve estar no formato DD/MM/AAAA.
    - O valor_total deve ser uma string contendo apenas números e um ponto como separador decimal (ex: "123.45").
    - A forma_pgto deve ser uma das seguintes strings: "dinheiro", "pix", "cartao", ou "outros".
    - Se um campo não for encontrado no texto, o valor correspondente no JSON deve ser null (o valor nulo do JSON).
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

