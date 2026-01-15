# 🖼️ Sistema de Processamento de Imagens com Google Cloud Vision API

Um sistema completo e escalável para processar imagens usando **Google Cloud Vision API**, com armazenamento em **Firestore**, notificações via **Pub/Sub** e interface web interativa.

## ✨ Características

✅ **Upload de Imagens** - Suporta drag & drop  
✅ **Análise Inteligente** - Vision API com 5 tipos de análise  
✅ **Armazenamento em NoSQL** - Firestore com estrutura otimizada  
✅ **Notificações em Tempo Real** - Pub/Sub para eventos  
✅ **API REST Completa** - Endpoints para todas as operações  
✅ **Frontend Responsivo** - Interface web moderna e interativa  
✅ **Escalável Serverless** - Cloud Functions + API REST  
✅ **Logging Detalhado** - Rastreamento completo de operações  

## 🚀 Quick Start (5 Minutos)

### 1. Pré-requisitos
```bash
# Python 3.7+
python --version

# Google Cloud SDK
gcloud version

# Autenticar
gcloud init
gcloud auth application-default login
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Executar em 2 Terminais

**Terminal 1 - APIs:**
```bash
python upload_api.py &
python api_resultados.py
```

**Terminal 2 - Frontend:**
```bash
python -m http.server 8000 --directory static
# Abrir http://localhost:8000
```

## 📚 Documentação Completa

| Documento | Descrição |
|-----------|-----------|
| [QUICKSTART.md](QUICKSTART.md) | Guia rápido (5 min) |
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | Instalação detalhada com GCP |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Visão geral da arquitetura |
| [fluxo_imagens_guide.md](fluxo_imagens_guide.md) | Guia completo em Python |

## 🏗️ Arquitetura

```
Frontend (HTML/JS) 
    ↓
Upload API (:5000) ← → Cloud Storage
    ↓                        ↓
                      Cloud Function
                            ↓
                       Vision API
                            ↓
                  Firestore ← → Pub/Sub
                            ↓
Resultados API (:5001) ← Firestore
```

## 📁 Estrutura do Projeto

```
projeto_cloud/
├── 📄 upload_api.py              # API para upload (Flask)
├── 📄 api_resultados.py          # API para consultar (Flask)
├── 📄 cloud_function_main.py     # Processamento na Cloud
├── 📄 notificacoes.py            # Subscriber Pub/Sub
├── 📄 test_api.py                # Testes interativos
├── 📄 requirements.txt           # Dependências
│
├── 📖 README.md                  # Este ficheiro
├── 📖 QUICKSTART.md              # Começar rápido
├── 📖 SETUP_GUIDE.md             # Guia de instalação
├── 📖 ARCHITECTURE.md            # Arquitetura
│
├── 📁 cloud-function/            # Para deploy Cloud Function
│   ├── main.py                   # (copiar cloud_function_main.py)
│   └── requirements.txt
│
└── 📁 static/                    # Frontend
    └── index.html                # (copiar frontend_index.html)
```

## 🔧 Componentes Principais

### 1. Upload API (`upload_api.py`)

API Flask para upload de imagens para Google Cloud Storage.

```bash
# Executar
python upload_api.py

# Usar
curl -X POST -F "file=@imagem.jpg" http://localhost:5000/upload
```

**Endpoints:**
- `POST /upload` - Fazer upload de imagem
- `GET /health` - Verificar status
- `GET /` - Documentação

### 2. Resultados API (`api_resultados.py`)

API Flask para consultar análises armazenadas no Firestore.

```bash
# Executar
python api_resultados.py

# Usar
curl http://localhost:5001/resultados
```

**Endpoints:**
- `GET /resultados` - Listar todas
- `GET /resultados/<id>` - Obter uma análise
- `GET /resultados/<id>/labels` - Obter labels
- `GET /resultados/<id>/texto` - Obter OCR
- `GET /resultados/<id>/rostos` - Obter rostos
- `GET /resultados/<id>/safe-search` - Análise segurança

### 3. Cloud Function (`cloud_function_main.py`)

Processamento serverless disparado por evento de upload.

**Análises realizadas:**
1. **Label Detection** - Detecção de objetos/elementos
2. **Text Detection** - OCR (reconhecimento de texto)
3. **Face Detection** - Detecção de rostos
4. **Safe Search** - Classificação de segurança
5. **Image Properties** - Cores dominantes

### 4. Frontend (`frontend_index.html`)

Interface web interativa com:
- Upload com drag & drop
- Visualização de resultados em grid
- Análise detalhada com tabs
- Visualização de cores
- Status em tempo real

### 5. Notificações (`notificacoes.py`)

Subscriber de Pub/Sub que escuta eventos de processamento e pode:
- Enviar emails
- Fazer webhooks
- Atualizar bases de dados
- Notificações push

## 💾 Base de Dados (Firestore)

### Coleção: `analises_imagens`

```json
{
  "nome_arquivo": "input/20240115_143022_foto.jpg",
  "data_processamento": "2024-01-15T14:30:22.123Z",
  "status": "processado",
  "total_labels": 15,
  "total_textos": 3,
  "total_rostos": 2,
  "resultados": {
    "labels": [...],
    "texto_completo": "...",
    "textos": [...],
    "rostos": [...],
    "cores_dominantes": [...],
    "safe_search": {...}
  }
}
```

## 🧪 Testando

### Opção 1: Menu Interativo
```bash
python test_api.py
```

### Opção 2: Frontend Web
```bash
# Servir static
python -m http.server 8000 --directory static
# Abrir http://localhost:8000
```

### Opção 3: cURL
```bash
# Upload
curl -X POST -F "file=@imagem.jpg" http://localhost:5000/upload

# Listar
curl http://localhost:5001/resultados

# Detalhes
curl http://localhost:5001/resultados/{id}/labels
```

## 🚀 Deploy em Produção

### Cloud Function
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

### APIs (Cloud Run)
```bash
# Criar Dockerfile e fazer deploy
gcloud run deploy upload-api \
  --source . \
  --platform managed \
  --region europe-west1
```

## 📊 Vision API - Tipos de Análise

| Análise | Descrição | Exemplo |
|---------|-----------|---------|
| **Labels** | Objetos/elementos detectados | pessoa, cão, carro |
| **OCR** | Texto na imagem | "Olá Mundo" |
| **Faces** | Rostos e expressões | 2 rostos, alegria: 8/10 |
| **Colors** | Cores dominantes | RGB(255, 100, 50) |
| **Safe Search** | Conteúdo adulto/violência | UNLIKELY |

## 🔐 Segurança

- ✅ Autenticação via `gcloud auth`
- ✅ Permissões IAM configuradas
- ✅ Variáveis de ambiente para secrets
- ✅ Validação de tipos de arquivo
- ✅ HTTPS em produção
- ✅ Rate limiting (opcional)

## 📈 Escalabilidade

- **Cloud Functions** - Escala automática
- **Firestore** - NoSQL escalável
- **Cloud Storage** - Armazenamento ilimitado
- **Pub/Sub** - Processamento assíncrono
- **Vision API** - Escalável automaticamente

## 🐛 Troubleshooting

### API não conecta
```bash
# Verificar se está em execução
curl http://localhost:5000/health
curl http://localhost:5001/health
```

### Erro de autenticação
```bash
# Reautenticar
gcloud auth application-default login
```

### Cloud Function falha
```bash
# Ver logs
gcloud functions logs read processar_imagem --limit 50
```

## 📚 Recursos Úteis

- [Vision API Docs](https://cloud.google.com/vision/docs)
- [Cloud Functions Docs](https://cloud.google.com/functions/docs)
- [Firestore Docs](https://cloud.google.com/firestore/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Google Cloud SDK](https://cloud.google.com/sdk)

## 🤝 Contribuindo

Sinta-se livre para fazer fork, melhorar e submeter pull requests!

## 📄 Licença

Este projeto está disponível sob a licença MIT.

## 👨‍💻 Autor

Sistema criado com IA em Janeiro 2026

---

## 🎯 Próximos Passos

1. ✅ Ler [QUICKSTART.md](QUICKSTART.md)
2. ✅ Executar os 4 passos iniciais
3. ✅ Fazer upload de uma imagem
4. ✅ Ver resultados em tempo real
5. ✅ Configurar Cloud Function para produção

**Pronto?** Comece com:
```bash
python upload_api.py
```

---

**Versão:** 1.0  
**Última atualização:** 15 de Janeiro, 2026  
**Status:** ✅ Pronto para usar
#   p r o j e c t o - c l o u d  
 #   p r o j e c t o - c l o u d  
 