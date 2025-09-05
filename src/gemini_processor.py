import json
import os
import urllib.request

# Obtém a chave da API das variáveis de ambiente
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

def analisar_com_gemini(texto_extraido: str) -> dict: # chama a API do Gemini
    print('❗Iniciando extração de dados com a API do Gemini...')

    # url da API
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}'

    # Prompt do Gemini com estrutura de regras melhorada
    prompt = f"""
    Analise o seguinte texto extraído de uma nota fiscal e devolva APENAS um objeto JSON válido.

    -> REGRAS ESTRITAS
    1.  **Campos Obrigatórios:** O JSON deve conter EXATAMENTE os seguintes campos: "nome_emissor", "CNPJ_emissor", "endereco_emissor", "CNPJ_CPF_consumidor", "data_emissao", "numero_nota_fiscal", "serie_nota_fiscal", "valor_total", "forma_pgto".
    2.  **Formato CNPJ/CPF:** O CNPJ deve ser formatado como "XX.XXX.XXX/XXXX-XX". O CPF deve ser "XXX.XXX.XXX-XX".
    3.  **Formato Data:** A "data_emissao" deve ser "DD/MM/AAAA".
    4.  **Formato Valor:** O "valor_total" deve ser uma string com ponto como separador decimal (ex: "123.45").
    5.  **Forma de Pagamento:** O campo "forma_pgto" deve ser apenas uma das seguintes opções: "dinheiro", "pix", "cartao", ou "outros".
    6.  **Valores Não Encontrados:** Se um campo não for encontrado no texto, o valor correspondente no JSON deve ser o valor `null`.
    7.  **Formato da Resposta:** A sua resposta deve ser APENAS o objeto JSON. Não inclua ```json no início ou fim, nem qualquer outro texto ou explicação.

    -> TEXTO PARA ANÁLISE
    ---
    {texto_extraido}
    ---
    """

    # requisição para a API
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    json_data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=json_data, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            response_body = json.loads(response.read())
            json_response_text = response_body['candidates'][0]['content']['parts'][0]['text']
            
            print("--- Resposta da LLM ---")
            print(json_response_text)
            
            # Converte a string de resposta em um dicionário
            return json.loads(json_response_text)
            
    except Exception as e:
        print(f"❌ Erro ao chamar a API do Gemini: {e}")
        # Detalha o erro
        if hasattr(e, 'read'): print(f"Detalhes do erro da API: {e.read().decode()}")
        return None

