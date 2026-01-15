# Quick Start - Começar Rapidamente

## ⚡ Passo a Passo Rápido (5 minutos)

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Autenticar com Google Cloud
```bash
# Se ainda não fez:
gcloud init
gcloud auth application-default login
```

### 3. Criar Bucket de Teste
```bash
gsutil mb gs://meu-bucket-imagens
```

### 4. Executar em 3 Terminais

**Terminal 1 - Upload API:**
```bash
python upload_api.py
```

**Terminal 2 - Resultados API:**
```bash
python api_resultados.py
```

**Terminal 3 - Subscriber (opcional):**
```bash
python notificacoes.py
```

### 5. Testar Upload
```bash
# PowerShell:
curl -X POST -F "file=@imagem.jpg" http://localhost:5000/upload

# Linux/Mac:
curl -X POST -F "file=@imagem.jpg" http://localhost:5000/upload
```

### 6. Ver Resultados
```bash
# Listar todas análises
curl http://localhost:5001/resultados

# Abrir no navegador
# http://localhost:5001/
```

## 📋 Checklist de Funcionalidades

- [x] Upload de imagens
- [x] Análise com Vision API (labels, texto, rostos, cores, segurança)
- [x] Armazenamento em Firestore
- [x] API REST para consultar resultados
- [x] Frontend web interativo
- [x] Notificações via Pub/Sub
- [x] Logging detalhado
- [x] Tratamento de erros

## 🔧 Para Produção (Próximas Etapas)

1. **Deploy Cloud Function:**
```bash
cd cloud-function
cp ../cloud_function_main.py main.py
gcloud functions deploy processar_imagem \
  --runtime python39 \
  --trigger-resource meu-bucket-imagens \
  --trigger-event google.storage.object.finalize \
  --entry-point processar_imagem \
  --region europe-west1
```

2. **Deploy APIs (App Engine ou Cloud Run):**
```bash
# Criar app.yaml
# Fazer deploy com: gcloud app deploy
```

3. **Configurar Segurança:**
- Adicionar autenticação
- Configurar CORS
- Adicionar rate limiting
- Usar variables de ambiente seguras

4. **Monitorar:**
- Configurar Cloud Logging
- Adicionar alertas
- Monitorar quota de Vision API

## 🆘 Suporte

- Documentação Google Cloud: https://cloud.google.com/docs
- Vision API: https://cloud.google.com/vision/docs
- Flask: https://flask.palletsprojects.com/

---

**Pronto para começar?** Execute os 4 primeiros passos acima! 🚀
