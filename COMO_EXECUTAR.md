# 🚀 Como Executar a Aplicação Completa

## ⚡ Quick Start (30 segundos)

### Passo 1: Instalar Dependências
```bash
cd c:\Projeto\projeto_cloud
pip install -r requirements.txt
```

### Passo 2: Executar a Aplicação
```bash
python app.py
```

### Passo 3: Abrir no Navegador
```
http://localhost:5000
```

**Pronto!** 🎉 Você já tem a aplicação completa com:
- ✅ Frontend web interativo
- ✅ Upload de imagens (drag & drop)
- ✅ Processamento automático com Vision API
- ✅ Armazenamento em Firestore
- ✅ Notificações Pub/Sub
- ✅ Visualização de resultados em tempo real

---

## 📊 O que a Aplicação Faz

```
FLUXO COMPLETO:

1. Utilizador faz upload de imagem
              ↓
2. App.py recebe o arquivo
              ↓
3. Vision API processa:
   - Detecção de objetos (labels)
   - OCR (reconhecimento de texto)
   - Detecção de rostos
   - Cores dominantes
   - Análise de segurança
              ↓
4. Resultados guardados no Firestore
              ↓
5. Notificação publicada em Pub/Sub
              ↓
6. Frontend atualiza automaticamente
              ↓
7. Utilizador vê resultados (com cliques interativos)
```

---

## 🖥️ Interface Web

### Upload
- Clique ou arraste a imagem
- Vê progresso em tempo real
- Arquivo processado automaticamente

### Resultados
- Grid com todas as análises
- Clique em qualquer resultado para ver detalhes

### Detalhes (5 abas)
- **Objetos**: Labels com score de confiança
- **Texto**: OCR detectado na imagem
- **Rostos**: Rostos detectados e emoções
- **Cores**: Cores dominantes da imagem
- **Segurança**: Análise de conteúdo adulto/violência

---

## 🧪 Testar a API Diretamente

```bash
# Fazer upload (Windows PowerShell)
$file = "C:\caminho\imagem.jpg"
$form = @{file = Get-Item $file}
Invoke-WebRequest -Uri "http://localhost:5000/upload" -Method POST -Form $form

# Ou com curl
curl -X POST -F "file=@imagem.jpg" http://localhost:5000/upload

# Obter resultados
curl http://localhost:5000/api/resultados
```

---

## 🔧 Alternativa: Executar Várias APIs Simultaneamente

Se prefere executar os serviços separadamente:

**Terminal 1:**
```bash
python app.py
```

**Terminal 2 (Notificações - opcional):**
```bash
python notificacoes.py
```

---

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'google'"
```bash
pip install -r requirements.txt
```

### Erro: "Firestore not available"
Certifique-se que:
1. Executou `gcloud auth application-default login`
2. Firestore database existe no GCP
3. Tem permissões corretas

### Erro: "Vision API is not enabled"
```bash
gcloud services enable vision.googleapis.com
```

### Porta 5000 já está em uso
```bash
# Mude a porta no app.py na última linha:
# app.run(debug=True, port=8080, host='127.0.0.1')
```

---

## 📝 Ficheiros Principais

| Ficheiro | Função |
|----------|--------|
| **app.py** | Aplicação completa (novo!) |
| upload_api.py | API upload isolada |
| api_resultados.py | API resultados isolada |
| notificacoes.py | Subscriber Pub/Sub |
| cloud_function_main.py | Para deploy em Cloud Function |

---

## ✨ Novidades (Comparado com Versão Anterior)

✅ **Tudo em 1 arquivo** - app.py integrado
✅ **Frontend embutido** - Sem servidor web separado
✅ **Processamento instantâneo** - Não precisa de Cloud Function
✅ **Mais rápido** - Resposta imediata no navegador
✅ **Sem complexidade** - Simples de executar

---

## 🚀 Para Produção

Quando estiver pronto para produção:

### Opção A: Cloud Run
```bash
gcloud run deploy image-analyzer \
  --source . \
  --platform managed \
  --region europe-west1
```

### Opção B: App Engine
```bash
# Criar app.yaml
gcloud app deploy
```

### Opção C: Cloud Function (sem mudar muito)
```bash
# Copiar cloud_function_main.py para Cloud Function
gcloud functions deploy processar_imagem \
  --runtime python39 \
  --trigger-resource meu-bucket-imagens \
  --trigger-event google.storage.object.finalize
```

---

**Pronto para começar?** Execute:
```bash
python app.py
```

Depois abra:
```
http://localhost:5000
```

**Boa sorte! 🎯**
