# Guia Rápido de Instalação e Configuração

## 1. Pré-requisitos

```bash
# Verificar se gcloud está instalado
gcloud version

# Verificar se Python está instalado (3.7+)
python --version
```

## 2. Autenticação Google Cloud

```bash
# Você já realizou isto antes, mas se precisa novamente:
gcloud init
gcloud auth application-default login
```

## 3. Instalar dependências Python

```bash
# Criar ambiente virtual (recomendado)
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## 4. Configurar GCP (Variáveis de Ambiente)

Criar arquivo `.env` na raiz do projeto:
```
PROJECT_ID=projectcloud-484416
BUCKET_INPUT=meu-bucket-imagens
BUCKET_OUTPUT=meu-bucket-resultados
PUBSUB_TOPIC=imagem-processada
FIRESTORE_COLLECTION=analises_imagens
```

## 5. Criar recursos no Google Cloud

### 5.1 - Criar Cloud Storage Buckets

```bash
# Bucket para imagens de entrada
gsutil mb gs://meu-bucket-imagens

# Bucket para resultados (opcional)
gsutil mb gs://meu-bucket-resultados

# Verificar buckets criados
gsutil ls
```

### 5.2 - Configurar permissões IAM

```bash
# Dar permissões ao Storage
gcloud projects add-iam-policy-binding projectcloud-484416 \
  --member=serviceAccount:projectcloud-484416@appspot.gserviceaccount.com \
  --role=roles/storage.admin

# Dar permissões ao Firestore
gcloud projects add-iam-policy-binding projectcloud-484416 \
  --member=serviceAccount:projectcloud-484416@appspot.gserviceaccount.com \
  --role=roles/datastore.admin

# Dar permissões ao Pub/Sub
gcloud projects add-iam-policy-binding projectcloud-484416 \
  --member=serviceAccount:projectcloud-484416@appspot.gserviceaccount.com \
  --role=roles/pubsub.admin

# Dar permissões à Vision API
gcloud projects add-iam-policy-binding projectcloud-484416 \
  --member=serviceAccount:projectcloud-484416@appspot.gserviceaccount.com \
  --role=roles/ml.viewer
```

### 5.3 - Habilitar APIs necessárias

```bash
# Cloud Storage
gcloud services enable storage.googleapis.com

# Vision API
gcloud services enable vision.googleapis.com

# Firestore
gcloud services enable firestore.googleapis.com

# Pub/Sub
gcloud services enable pubsub.googleapis.com

# Cloud Functions
gcloud services enable cloudfunctions.googleapis.com

# Cloud Build
gcloud services enable cloudbuild.googleapis.com
```

### 5.4 - Criar Pub/Sub Topic e Subscription

```bash
# Criar tópico
gcloud pubsub topics create imagem-processada \
  --project projectcloud-484416

# Criar subscription
gcloud pubsub subscriptions create imagem-processada-sub \
  --topic imagem-processada \
  --project projectcloud-484416
```

### 5.5 - Criar Firestore Database

```bash
# Criar database (escolher modo "Native")
gcloud firestore databases create --location=europe-west1
```

## 6. Deploy da Cloud Function

```bash
# Navegar para pasta cloud-function
cd cloud-function

# Copiar os arquivos necessários
cp ../cloud_function_main.py main.py

# Fazer deploy
gcloud functions deploy processar_imagem \
  --runtime python39 \
  --trigger-resource meu-bucket-imagens \
  --trigger-event google.storage.object.finalize \
  --entry-point processar_imagem \
  --region europe-west1 \
  --project projectcloud-484416 \
  --timeout 300 \
  --memory 2GB

# Voltar à pasta principal
cd ..
```

## 7. Executar APIs Localmente

### Terminal 1 - API de Upload

```bash
python upload_api.py
# A API estará em http://localhost:5000
```

### Terminal 2 - API de Resultados

```bash
python api_resultados.py
# A API estará em http://localhost:5001
```

### Terminal 3 - Subscriber de Notificações

```bash
python notificacoes.py
# Escutará por notificações do Pub/Sub
```

### Terminal 4 - Servir Frontend

```bash
# Opção 1: Python simples
python -m http.server 8000 --directory static
# Abrir http://localhost:8000

# Opção 2: Usando Flask (colocar index.html em static/)
flask run --port 8001
```

## 8. Testar o Fluxo Completo

### 8.1 - Via Frontend
1. Abrir http://localhost:8000 (ou 8001 dependendo do servidor)
2. Fazer upload de uma imagem
3. Ver resultados em tempo real

### 8.2 - Via curl

```bash
# Upload
curl -X POST -F "file=@imagem.jpg" http://localhost:5000/upload

# Listar resultados
curl http://localhost:5001/resultados

# Obter resultado específico
curl http://localhost:5001/resultados/{doc_id}

# Obter apenas labels
curl http://localhost:5001/resultados/{doc_id}/labels
```

## 9. Monitorar Logs

### Cloud Function
```bash
gcloud functions logs read processar_imagem \
  --region europe-west1 \
  --limit 50
```

### Firestore
```bash
# Listar documentos
gcloud firestore documents list --collection-id=analises_imagens
```

### Pub/Sub
```bash
# Ver mensagens na subscription
gcloud pubsub subscriptions pull imagem-processada-sub --limit=10
```

## 10. Variáveis de Ambiente Recomendadas

Criar `.env` com:
```
PROJECT_ID=projectcloud-484416
BUCKET_NAME=meu-bucket-imagens
REGION=europe-west1
FLASK_ENV=development
FLASK_DEBUG=True
```

## 11. Estrutura Final de Pastas

```
projeto_cloud/
├── upload_api.py              # API de upload
├── api_resultados.py          # API de resultados
├── notificacoes.py            # Subscriber Pub/Sub
├── cloud_function_main.py     # Cloud Function (copiar para cloud-function/main.py)
├── requirements.txt           # Dependências Python
├── .env                       # Variáveis de ambiente
├── .gitignore                 # Git ignore
├── cloud-function/            # Pasta para deploy da função
│   ├── main.py               # (copiar cloud_function_main.py aqui)
│   └── requirements.txt       # Dependências da função
├── static/                    # Frontend
│   └── index.html            # (copiar de frontend_index.html)
└── README.md                  # Documentação (este arquivo)
```

## 12. Troubleshooting

### Erro: "gcloud not found"
- Instalar Google Cloud SDK: https://cloud.google.com/sdk/docs/install-gcloud-cli

### Erro: "Permission denied"
- Verificar permissões IAM no console GCP
- Executar `gcloud auth application-default login`

### Erro: "Bucket not found"
- Criar bucket: `gsutil mb gs://nome-bucket`
- Verificar nome correto no código

### Erro: "Firestore not found"
- Habilitar API: `gcloud services enable firestore.googleapis.com`
- Criar database: `gcloud firestore databases create`

### Cloud Function lenta
- Aumentar memória: `--memory 2GB`
- Aumentar timeout: `--timeout 300`
- Verificar logs: `gcloud functions logs read processar_imagem`

## 13. Próximos Passos

- [ ] Configurar autenticação de utilizador (Firebase Auth)
- [ ] Adicionar base de dados de utilizadores
- [ ] Implementar envio de emails com SendGrid
- [ ] Adicionar notificações push
- [ ] Implementar sistema de quotas/limites
- [ ] Adicionar testes automatizados
- [ ] Implementar CI/CD (GitHub Actions, Cloud Build)
- [ ] Configurar monitoring e alertas
