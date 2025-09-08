# 📄 API REST de Processamento de Notas Fiscais

![Python](https://img.shields.io/badge/Python-3.13-blue) ![AWS Lambda](https://img.shields.io/badge/AWS%20Lambda-serverless-orange) ![AWS S3](https://img.shields.io/badge/AWS%20S3-storage-yellow) ![Textract](https://img.shields.io/badge/AWS%20Textract-OCR-red)

---

## Sumário

1. [Descrição](#descrição)
2. [Funcionalidades](#funcionalidades)
3. [Tecnologias](#tecnologias)
4. [Estrutura do Projeto](#estrutura-do-projeto)
5. [Instalação e Deploy](#instalação-e-deploy)
6. [Endpoint](#endpoint)
7. [Exemplo de Uso](#exemplo-de-uso)
8. [Logs](#logs)
9. [Considerações](#considerações)
10. [Dificuldades e Aprendizados](#dificuldades-e-aprendizados)

---

## Descrição

API REST em Python que recebe **imagens ou PDFs de notas fiscais eletrônicas simplificadas**, armazena no **S3**, extrai texto com **Amazon Textract** e refina os dados utilizando **LLM (Gemini)** para gerar JSON estruturado.

Arquivos são automaticamente movidos dentro do bucket S3 conforme **forma de pagamento**:

* `dinheiro/` → notas pagas em dinheiro ou PIX
* `outros/` → notas com outras formas de pagamento

Todos os logs de processamento são gravados no **CloudWatch**.

---

## Funcionalidades

* Recebe arquivos via POST (`multipart/form-data`)
* Armazena notas no S3
* Extrai texto usando **Amazon Textract**
* Refinamento e extração de dados com **LLM Gemini**
* Classificação de arquivos no bucket (`dinheiro/` ou `outros/`)
* Retorno JSON com os dados estruturados da nota fiscal
* Registro de logs detalhados no **CloudWatch**

---

## Tecnologias

* Python 3.13 
* AWS Lambda 
* AWS S3 
* Amazon Textract 
* Gemini LLM 
* CloudWatch 

---

## Estrutura do Projeto

```
projeto-sprint-4-5-6/
│
├─ src/
│   ├─ lambda_function.py       # Função Lambda principal
│   ├─ textract_processor.py    # Extração de texto via Textract
│   └─ gemini_processor.py      # Refinamento de dados via LLM
│
├─ README.md
└─ requirements.txt
```

---

## Instalação e Deploy

1. Criar bucket S3 e configurar variável de ambiente:

```bash
BUCKET_NAME=<nome_do_bucket>
```

2. Configurar chave da LLM Gemini:

```bash
GEMINI_API_KEY=<sua_chave_api>
```

3. Instalar dependências para empacotar:

```bash
pip install multipart boto3 -t ./package
```

4. Empacotar os arquivos e fazer deploy na Lambda:

```bash
cd package
zip -r ../lambda-deploy.zip .
cd ..
zip -g lambda-deploy.zip src/*
```

5. Criar API Gateway com método POST apontando para `/api/v1/invoice`.

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

* Campo: `file` → arquivo PDF ou imagem da nota fiscal.

---

## Exemplo de Uso

**Usando curl**:

```bash
curl -X POST https://1egnwizx5d.execute-api.us-east-1.amazonaws.com/squad6/api/v1/invoice \
  -F "file=@nota.pdf"
```

**Resposta JSON**:

```json
{
  "status": "sucesso",
  "respostas": [
    {
      "arquivo": "nota.pdf",
      "texto_refinado": {
        "nome_emissor": "Empresa XYZ Ltda",
        "CNPJ_emissor": "12.345.678/0001-90",
        "endereco_emissor": "Rua Exemplo, 123",
        "CNPJ_CPF_consumidor": "123.456.789-00",
        "data_emissao": "01/09/2025",
        "numero_nota_fiscal": "1234",
        "serie_nota_fiscal": "1",
        "valor_total": "123.45",
        "forma_pgto": "pix",
        "s3_location": "s3://bucket/dinheiro/nota.pdf"
      }
    }
  ],
  "erros": []
}
```

---

## Logs

* Todos os logs de processamento são gravados automaticamente no **CloudWatch**.
* Incluem sucesso, erros e caminho do arquivo no S3.

---

## Considerações

* Suporta **múltiplos arquivos** por requisição.
* Arquivos são armazenados com **UUID** para evitar conflitos de nome.
* A lógica de LLM pode ser refinada para diferentes formatos de nota fiscal.
* Estrutura modular para fácil manutenção e expansão.

---

## Dificuldades e Aprendizados

*Durante o desenvolvimento deste projeto, nos deparamos com alguns desafios interessantes que acabaram se tornando grandes oportunidades de aprendizado. Trabalhar com uploads `multipart/form-data` no AWS Lambda exigiu algumas adaptações para que os arquivos enviados fossem recebidos e processados corretamente. Extrair dados precisos com o Amazon Textract também trouxe suas dificuldades, já que cada nota fiscal podia ter um layout diferente, o que exigiu ajustes finos na análise dos documentos. Além disso, o refinamento dos dados usando a LLM Gemini demandou compreensão sobre como o modelo interpreta e estrutura as informações, e ajustes foram necessários para garantir resultados consistentes. A organização dos arquivos no S3, com diretórios dinâmicos e identificadores únicos, foi outro ponto importante para evitar conflitos e manter a integridade dos dados. Por fim, integrar o API Gateway para lidar com requisições multipart e encaminhá-las corretamente para a Lambda foi essencial para que a API funcionasse de forma confiável. Apesar de todos esses desafios, cada um deles nos trouxe aprendizados valiosos e fortaleceu nossas habilidades em soluções serverless na AWS.*

---
