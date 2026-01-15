# 📊 Fluxo Completo de Processamento de Imagens com Google Cloud

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CLIENTE / FRONTEND                              │
│  (Navegador Web)                                                        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                 │
                    ▼                                 ▼
         ┌──────────────────────┐        ┌──────────────────────┐
         │   UPLOAD API         │        │  RESULTADOS API      │
         │ (Python Flask)       │        │  (Python Flask)      │
         │ :5000                │        │  :5001               │
         └──────────┬───────────┘        └──────────┬───────────┘
                    │                               │
                    │ upload                        │ consulta
                    │                               │
                    ▼                               ▼
    ┌───────────────────────────────────────────────────────────────┐
    │  GOOGLE CLOUD STORAGE (gs://meu-bucket-imagens)             │
    │                                                               │
    │  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐         │
    │  │   input/    │  │  processing/ │  │   output/   │         │
    │  │             │  │              │  │             │         │
    │  └─────────────┘  └──────────────┘  └─────────────┘         │
    └────────────┬───────────────────────────────────────────────────┘
                 │
      ┌──────────┴─────────────────┐
      │ Evento: object.finalized   │
      └──────────┬─────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────────────────┐
    │     CLOUD FUNCTION (processar_imagem)       │
    │     (Python)                                 │
    │                                              │
    │  1️⃣  Lê imagem do Storage                   │
    │  2️⃣  Chama Vision API                       │
    │  3️⃣  Guarda resultados                      │
    │  4️⃣  Publica notificação                    │
    └────────────┬─────────────┬──────────┬────────┘
                 │             │          │
        ┌────────▼──┐  ┌───────▼────┐  ┌─▼──────────────┐
        │ Vision API│  │  Firestore │  │  Pub/Sub Topic │
        │           │  │            │  │                │
        │ - Labels  │  │Analises    │  │ imagem-        │
        │ - OCR     │  │_imagens    │  │ processada     │
        │ - Faces   │  │            │  │                │
        │ - Colors  │  │(DB)        │  └─┬──────────────┘
        │ - Safe    │  │            │    │
        └───────────┘  └────────────┘    │
                                         ▼
                         ┌──────────────────────────┐
                         │   Subscriber (opcional)  │
                         │   (notificacoes.py)      │
                         │                          │
                         │ Envia emails, webhooks   │
                         │ ou notificações push     │
                         └──────────────────────────┘
```

---

## 📁 Estrutura de Ficheiros

```
projeto_cloud/
│
├── 📄 upload_api.py                    # API Flask para upload
├── 📄 api_resultados.py               # API Flask para consultar resultados
├── 📄 cloud_function_main.py          # Código da Cloud Function
├── 📄 notificacoes.py                 # Subscriber de Pub/Sub
├── 📄 test_api.py                     # Testes interativos
│
├── 📄 requirements.txt                # Dependências Python
├── 📄 .env                            # Variáveis de ambiente
├── 📄 .gitignore                      # Git ignore
│
├── 📖 README.md                       # Guia completo
├── 📖 SETUP_GUIDE.md                  # Guia de instalação
├── 📖 QUICKSTART.md                   # Começar rapidamente
├── 📖 ARCHITECTURE.md                 # Este ficheiro
│
├── 📁 cloud-function/                 # Pasta para deploy
│   ├── main.py                        # Copiar cloud_function_main.py
│   └── requirements.txt               # Dependências da função
│
└── 📁 static/                         # Frontend
    └── index.html                     # Interface web (copiar frontend_index.html)
```

---

## 🔄 Fluxo de Dados

### 1️⃣ Upload de Imagem

```
Utilizador
    │
    ├─► Frontend (index.html)
    │        │
    │        └─► POST /upload
    │             (multipart/form-data)
    │
    └─► API Upload (upload_api.py)
         │
         └─► Google Cloud Storage
              (gs://meu-bucket-imagens/input/)
```

### 2️⃣ Processamento Automático

```
Cloud Storage Event
(object.finalized)
    │
    └─► Cloud Function (main.py)
         │
         ├─► 1. Ler imagem do Storage
         │
         ├─► 2. Vision API
         │   ├─ Label Detection (objetos)
         │   ├─ Text Detection (OCR)
         │   ├─ Face Detection (rostos)
         │   ├─ Safe Search (segurança)
         │   └─ Image Properties (cores)
         │
         ├─► 3. Firestore
         │   └─ Guardar resultados
         │
         └─► 4. Pub/Sub
             └─ Notificação publicada
```

### 3️⃣ Consulta de Resultados

```
Utilizador
    │
    └─► Frontend (index.html)
         │
         └─► GET /resultados
              (API Resultados)
              │
              └─► Firestore
                  └─► Devolver dados
```

---

## 🚀 Endpoints da API

### Upload API (`:5000`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/upload` | Fazer upload de imagem |
| GET | `/health` | Verificar status |
| GET | `/` | Documentação |

### Resultados API (`:5001`)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/resultados` | Listar todas as análises |
| GET | `/resultados/<id>` | Obter análise completa |
| GET | `/resultados/search?nome=xxx` | Buscar por nome |
| GET | `/resultados/<id>/labels` | Obter labels |
| GET | `/resultados/<id>/texto` | Obter OCR |
| GET | `/resultados/<id>/rostos` | Obter rostos |
| GET | `/resultados/<id>/safe-search` | Obter análise segurança |
| GET | `/health` | Verificar status |
| GET | `/` | Documentação |

---

## 📊 Dados Armazenados no Firestore

### Coleção: `analises_imagens`

```javascript
{
  "id": "documento_auto_gerado",
  "nome_arquivo": "input/20240115_143022_foto.jpg",
  "data_processamento": timestamp,
  "status": "processado",
  "total_labels": 15,
  "total_textos": 3,
  "total_rostos": 2,
  
  "resultados": {
    "labels": [
      {
        "descricao": "pessoa",
        "score": 0.95,
        "mid": "m.01g317"
      },
      ...
    ],
    
    "texto_completo": "Texto detectado na imagem",
    "textos": [
      {
        "texto": "Olá",
        "confianca": 0.98
      },
      ...
    ],
    
    "rostos": [
      {
        "confianca": 0.92,
        "alegria": 8,
        "surpresa": 2,
        "raiva": 1,
        "tristeza": 0
      },
      ...
    ],
    
    "cores_dominantes": [
      {
        "cor_rgb": { "red": 255, "green": 200, "blue": 100 },
        "score": 0.45,
        "pixel_fraction": 0.35
      },
      ...
    ],
    
    "safe_search": {
      "adulto": "VERY_UNLIKELY",
      "violencia": "UNLIKELY",
      "spam": "UNLIKELY",
      "conteudo_medico": "UNLIKELY"
    }
  }
}
```

### Coleção: `notificacoes` (opcional)

```javascript
{
  "arquivo": "input/20240115_143022_foto.jpg",
  "documento_firestore": "abc123...",
  "total_labels": 15,
  "total_textos": 3,
  "total_rostos": 2,
  "timestamp": timestamp,
  "status": "processado_sucesso"
}
```

---

## 🔐 Segurança

### Autenticação
- Usar `gcloud auth application-default login`
- Variáveis de ambiente para credenciais
- IAM Roles configuradas

### Permissões IAM Necessárias
- `roles/storage.admin` - Google Cloud Storage
- `roles/datastore.admin` - Firestore
- `roles/pubsub.admin` - Pub/Sub
- `roles/ml.viewer` - Vision API
- `roles/cloudfunctions.developer` - Cloud Functions

### Boas Práticas
- Validar tipos de arquivo
- Limitar tamanho de upload
- Rate limiting nas APIs
- HTTPS em produção
- Tokens JWT para autenticação
- CORS configurado

---

## 📈 Escalabilidade

### Serverless Architecture
- **Cloud Functions**: Escalável automaticamente
- **Firestore**: NoSQL escalável
- **Cloud Storage**: Armazenamento ilimitado
- **Pub/Sub**: Mensageria em tempo real
- **Vision API**: Escalável automaticamente

### Limites e Quotas
- Vision API: Checar quotas no console GCP
- Firestore: Limite de reads/writes por segundo
- Storage: Sem limite de armazenamento
- Pub/Sub: Sem limite de mensagens

---

## 🧪 Testando Localmente

### Opção 1: Usar `test_api.py`
```bash
python test_api.py
# Menu interativo com vários testes
```

### Opção 2: Usar `curl`
```bash
# Upload
curl -X POST -F "file=@imagem.jpg" http://localhost:5000/upload

# Listar resultados
curl http://localhost:5001/resultados

# Obter resultado específico
curl http://localhost:5001/resultados/{id}
```

### Opção 3: Frontend Web
```bash
# Abrir em navegador
http://localhost:8000
```

---

## 🔍 Monitoramento e Logs

### Cloud Function
```bash
gcloud functions logs read processar_imagem --limit 50
```

### Firestore
```bash
gcloud firestore documents list --collection-id=analises_imagens
```

### Cloud Storage
```bash
gsutil ls -r gs://meu-bucket-imagens/
```

### Pub/Sub
```bash
gcloud pubsub subscriptions pull imagem-processada-sub --limit 10
```

---

## 📱 Frontend Capabilities

✅ Upload de imagens (drag & drop)
✅ Visualização de resultados em grid
✅ Análise interativa com tabs
✅ Visualização de cores
✅ Exibição de labels com score
✅ Exibição de OCR
✅ Exibição de rostos detectados
✅ Análise de segurança
✅ Paginação de resultados
✅ Busca por nome
✅ Dark mode ready

---

## 🚀 Próximas Melhorias

- [ ] Autenticação de utilizador (Firebase)
- [ ] Dashboard de estatísticas
- [ ] Histórico de uploads
- [ ] Exportação de resultados (PDF, CSV)
- [ ] Filtros avançados
- [ ] Comparação de imagens
- [ ] Batch processing
- [ ] Webhooks customizados
- [ ] API documentation (Swagger)
- [ ] CI/CD pipeline (GitHub Actions)

---

## 📚 Referências

- [Google Cloud Vision API](https://cloud.google.com/vision/docs)
- [Google Cloud Storage](https://cloud.google.com/storage/docs)
- [Google Cloud Firestore](https://cloud.google.com/firestore/docs)
- [Google Cloud Pub/Sub](https://cloud.google.com/pubsub/docs)
- [Cloud Functions](https://cloud.google.com/functions/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

**Criado em:** 15 de Janeiro, 2026
**Versão:** 1.0
**Autor:** Sistema de IA
