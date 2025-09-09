
# 📄 API REST de Processamento de Notas Fiscais

![Python](https://img.shields.io/badge/Python-3.13-blue) ![AWS Lambda](https://img.shields.io/badge/AWS%20Lambda-serverless-orange) ![AWS S3](https://img.shields.io/badge/AWS%20S3-storage-yellow) ![Textract](https://img.shields.io/badge/AWS%20Textract-OCR-red) ![Gemini](https://img.shields.io/badge/Gemini-LLM-purple)

---

## Sumário

1. [Descrição](#descrição)
2. [Tecnologias](#tecnologias)
3. [Estrutura do Projeto](#estrutura-do-projeto)
4. [Instalação e Deploy](#instalação-e-deploy)
5. [Endpoint](#endpoint)
6. [Exemplo de Uso](#exemplo-de-uso)
7. [Como Utilizar a Aplicação](#como-utilizar-a-aplicação)
8. [Logs](#logs)
9. [Dificuldades e Aprendizados](#dificuldades-e-aprendizados)

---

## Descrição

API REST em Python que recebe **imagens de notas fiscais eletrônicas simplificadas** (ex: JPG, PNG), armazena no **Amazon S3**, extrai texto com **Amazon Textract** e refina os dados utilizando **LLM (Gemini)** para gerar um JSON estruturado.

Arquivos são automaticamente movidos dentro do bucket S3 conforme **forma de pagamento**:

* `dinheiro/` → notas pagas em **dinheiro ou PIX**
* `outros/` → notas com outras formas de pagamento

Todos os logs de processamento são gravados no **CloudWatch**.

---

## Tecnologias

* Python **3.13**
* AWS Lambda
* Amazon S3
* Amazon Textract
* Gemini LLM
* API Gateway
* CloudWatch

---

## Estrutura do Projeto

```
projeto-sprint-4-5-6/
├─ lambda_function.py       # Função Lambda principal (upload + fluxo completo)
├─ textract_processor.py    # Extração de texto via Textract
├─ gemini_processor.py      # Refinamento de dados via LLM
│
├─ README.md               
└─ requirements.txt         
```

---

## Instalação e Deploy

### 1. Criar bucket no S3

```bash
aws s3 mb s3://<nome-do-bucket>
```

---

### 2. Configurar variáveis de ambiente na Lambda

```bash
BUCKET_NAME=<nome_do_bucket>
GEMINI_API_KEY=<sua_chave_gemini>
```

---

### 3. Empacotar dependências

```bash
zip -r lambda-deploy.zip src/*
```

---

### 4. Criar API Gateway

* Método: **POST**
* Caminho: `/api/v1/invoice`
* Integração: **Lambda**

---

## Endpoint

### POST `/api/v1/invoice`

**URL de Produção**:

```
https://1egnwizx5d.execute-api.us-east-1.amazonaws.com/squad6/api/v1/invoice
```

**Headers**:

```
Content-Type: multipart/form-data
```

**Body**:

* Campo: `file` → imagem da nota fiscal (**JPG, PNG**).

---

## Exemplo de Uso

### Via curl

```bash
curl.exe --location --request POST "https://1egnwi2x5d.execute-api.us-east-1.amazonaws.com/squad6/api/v1/invoice" --form "file=@/seu/caminho/do/arquivo.jpg" | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

### Via Postman / Insomnia

1. Selecione método **POST**
2. Cole a URL do endpoint
3. Vá em **Body → form-data**
4. Adicione o campo:

   * Key: `file`
   * Type: File
   * Value: selecione a nota (`.jpg` ou `.png`)
5. Envie a requisição

---

### Resposta JSON

```json
    
 {
        "nome_emissor": "Empresa XYZ Ltda",
        "CNPJ_emissor": "12.345.678/0001-90",
        "endereco_emissor": "Rua Exemplo, 123",
        "CNPJ_CPF_consumidor": "123.456.789-00",
        "data_emissao": "01/09/2025",
        "numero_nota_fiscal": "1234",
        "serie_nota_fiscal": "1",
        "valor_total": "123.45",
         "forma_pgto": "pix"
}

```

---

## Como Utilizar a Aplicação

1. Prepare uma nota fiscal em **imagem (JPG ou PNG)**
2. Envie para o endpoint via `curl`, Postman ou Insomnia
3. O sistema:

   * Recebe e valida o upload
   * Armazena no **S3** em `recebidos/`
   * Extrai texto com **Textract**
   * Refina os dados com o **Gemini**
   * Move a imagem para `dinheiro/` ou `outros/`
   * Retorna JSON estruturado com todos os campos

> 🔎 Caso o upload falhe, a API retorna os erros com logs no **CloudWatch**.

---

## Logs

* Disponíveis no **AWS CloudWatch**
* Incluem:

  * Sucesso no upload
  * Caminho final do arquivo no S3
  * Erros de processamento (Textract, Gemini, etc.)

---

## Dificuldades e Aprendizados

Durante o desenvolvimento:

* Upload `multipart/form-data` no AWS Lambda exigiu parsing manual com a lib nativa `email`.
* O Amazon Textract retorna dados diferentes dependendo do layout da nota → ajustes foram necessários.
* O Gemini foi essencial para **estruturar campos inconsistentes** e gerar JSON confiável.
* Organização no S3 usando **pastas dinâmicas** e **UUIDs** trouxe robustez.
* Configuração correta do API Gateway foi fundamental para lidar com uploads binários.

---
