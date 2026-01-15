# Fluxo de Processamento de Imagens com Google Cloud - Guia em Python

## Arquitetura do Fluxo
```
Upload Imagem (Frontend/API) 
    ↓
Google Cloud Storage (gs://bucket/input/)
    ↓ (evento: object finalized)
Cloud Function (Python)
    ↓
Vision API (análise da imagem)
    ↓
Firestore/BigQuery (armazenar resultados)
    ↓
Pub/Sub (notificação - opcional)
    ↓
Notificação ao Utilizador
```

---

## PASSO 1: Upload de Imagem para Cloud Storage

### 1.1 - Configuração Inicial
```bash
pip install google-cloud-storage
pip install flask
```

### 1.2 - API Backend para Upload
**arquivo: `upload_api.py`**
```python
from flask import Flask, request, jsonify
from google.cloud import storage
import os
from datetime import datetime

app = Flask(__name__)

# Configuração
BUCKET_NAME = "meu-bucket-imagens"
INPUT_FOLDER = "input/"

# Inicializar cliente do Storage
storage_client = storage.Client(project="projectcloud-484416")
bucket = storage_client.bucket(BUCKET_NAME)

@app.route('/upload', methods=['POST'])
def upload_imagem():
    """
    Endpoint para upload de imagem
    Esperado: arquivo em multipart/form-data
    """
    try:
        # Validar se arquivo foi enviado
        if 'file' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'erro': 'Nome de arquivo vazio'}), 400
        
        # Gerar nome único com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"{INPUT_FOLDER}{timestamp}_{file.filename}"
        
        # Fazer upload para Cloud Storage
        blob = bucket.blob(nome_arquivo)
        blob.upload_from_file(file)
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Imagem {nome_arquivo} enviada com sucesso',
            'blob_path': nome_arquivo,
            'bucket': BUCKET_NAME
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### 1.3 - Testar Upload via curl
```bash
curl -X POST -F "file=@/caminho/para/imagem.jpg" http://localhost:5000/upload
```

---

## PASSO 2: Cloud Function Disparada por Evento de Upload

### 2.1 - Criar Cloud Function no GCP
```bash
# Criar pasta para a função
mkdir cloud-function
cd cloud-function
```

### 2.2 - main.py (Código da Cloud Function)
**arquivo: `cloud-function/main.py`**
```python
import functions_framework
from google.cloud import storage
from google.cloud import vision
from google.cloud import firestore
from google.cloud import pubsub_v1
import json
from datetime import datetime

# Inicializar clientes
storage_client = storage.Client()
vision_client = vision.ImageAnnotatorClient()
db = firestore.Client()
publisher_client = pubsub_v1.PublisherClient()

# Configurações
BUCKET_NAME = "meu-bucket-imagens"
OUTPUT_BUCKET = "meu-bucket-resultados"
PROJECT_ID = "projectcloud-484416"
TOPIC_ID = "imagem-processada"

@functions_framework.cloud_event
def processar_imagem(cloud_event):
    """
    Função disparada quando uma imagem é enviada para Cloud Storage
    Event type: google.cloud.storage.object.v1.finalized
    """
    try:
        # Extrair informações do evento
        bucket_name = cloud_event.data["bucket"]
        file_name = cloud_event.data["name"]
        
        print(f"Processando imagem: {file_name} do bucket: {bucket_name}")
        
        # PASSO 3: Ler a imagem do Storage
        imagem_base64 = ler_imagem_storage(bucket_name, file_name)
        
        # PASSO 4: Chamar Vision API
        resultados = analisar_com_vision_api(imagem_base64)
        
        # PASSO 5: Guardar resultados no Firestore
        doc_id = guardar_resultado_firestore(file_name, resultados)
        
        # PASSO 6: Publicar em Pub/Sub (opcional)
        publicar_notificacao(file_name, doc_id, resultados)
        
        print(f"Imagem {file_name} processada com sucesso!")
        return {"status": "sucesso", "documento": doc_id}
        
    except Exception as e:
        print(f"Erro ao processar imagem: {str(e)}")
        return {"status": "erro", "mensagem": str(e)}, 500


def ler_imagem_storage(bucket_name, file_name):
    """Lê a imagem do Google Cloud Storage"""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    imagem_bytes = blob.download_as_bytes()
    return imagem_bytes


def analisar_com_vision_api(imagem_bytes):
    """Chama Google Cloud Vision API para análise"""
    
    # Criar request para Vision API
    image = vision.Image(content=imagem_bytes)
    
    resultados = {}
    
    # 1. Label Detection (Detecção de Objetos/Rótulos)
    response = vision_client.label_detection(image=image)
    resultados['labels'] = [
        {
            'descricao': label.description,
            'score': float(label.score)
        }
        for label in response.label_annotations
    ]
    
    # 2. Text Detection (Detecção de Texto - OCR)
    response = vision_client.text_detection(image=image)
    resultados['textos'] = [
        {
            'texto': text.description,
            'confianca': float(text.confidence)
        }
        for text in response.text_annotations
    ]
    
    # 3. Face Detection (Detecção de Rostos - opcional)
    response = vision_client.face_detection(image=image)
    resultados['rostos'] = [
        {
            'confianca': float(face.detection_confidence),
            'alegria': float(face.joy_likelihood)
        }
        for face in response.face_annotations
    ]
    
    # 4. Safe Search Detection (Classificação de conteúdo seguro)
    response = vision_client.safe_search_detection(image=image)
    resultados['safe_search'] = {
        'adulto': response.safe_search_annotation.adult,
        'violencia': response.safe_search_annotation.violence,
        'spam': response.safe_search_annotation.spam
    }
    
    return resultados


def guardar_resultado_firestore(nome_arquivo, resultados):
    """Guarda os resultados de análise no Firestore"""
    
    dados = {
        'nome_arquivo': nome_arquivo,
        'data_processamento': datetime.now(),
        'resultados': resultados,
        'status': 'processado'
    }
    
    # Adicionar documento à coleção 'analises_imagens'
    _, doc_ref = db.collection('analises_imagens').add(dados)
    
    print(f"Resultado guardado no Firestore com ID: {doc_ref.id}")
    return doc_ref.id


def publicar_notificacao(nome_arquivo, doc_id, resultados):
    """Publica mensagem em Pub/Sub para notificar outros serviços"""
    
    topic_path = publisher_client.topic_path(PROJECT_ID, TOPIC_ID)
    
    mensagem = {
        'nome_arquivo': nome_arquivo,
        'documento_firestore': doc_id,
        'tempo_processamento': datetime.now().isoformat(),
        'total_labels': len(resultados.get('labels', [])),
        'total_textos': len(resultados.get('textos', []))
    }
    
    # Publicar mensagem
    future = publisher_client.publish(
        topic_path, 
        json.dumps(mensagem).encode('utf-8')
    )
    
    print(f"Notificação publicada com ID: {future.result()}")


def enviar_email_notificacao(email_usuario, doc_id):
    """Função para enviar email ao utilizador (pode chamar SendGrid, etc)"""
    # Implementação específica de envio de email
    pass
```

### 2.3 - requirements.txt
**arquivo: `cloud-function/requirements.txt`**
```
google-cloud-storage==2.10.0
google-cloud-vision==3.5.0
google-cloud-firestore==2.11.0
google-cloud-pubsub==2.18.0
functions-framework==3.5.0
```

### 2.4 - Fazer Deploy da Cloud Function
```bash
gcloud functions deploy processar_imagem \
  --runtime python39 \
  --trigger-resource meu-bucket-imagens \
  --trigger-event google.storage.object.finalize \
  --entry-point processar_imagem \
  --region europe-west1 \
  --project projectcloud-484416
```

---

## PASSO 3: Aplicação Frontend para Visualizar Resultados

### 3.1 - API para Consultar Resultados
**arquivo: `api_resultados.py`**
```python
from flask import Flask, jsonify, request
from google.cloud import firestore

app = Flask(__name__)
db = firestore.Client()

@app.route('/resultados/<doc_id>', methods=['GET'])
def obter_resultado(doc_id):
    """Obter resultado de uma análise específica"""
    try:
        doc = db.collection('analises_imagens').document(doc_id).get()
        
        if not doc.exists:
            return jsonify({'erro': 'Documento não encontrado'}), 404
        
        return jsonify(doc.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/resultados', methods=['GET'])
def listar_resultados():
    """Listar todas as análises realizadas"""
    try:
        docs = db.collection('analises_imagens').order_by(
            'data_processamento', 
            direction=firestore.Query.DESCENDING
        ).limit(20).stream()
        
        resultados = []
        for doc in docs:
            resultado = doc.to_dict()
            resultado['id'] = doc.id
            resultados.append(resultado)
        
        return jsonify(resultados), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
```

### 3.2 - Frontend HTML/JS Simples
**arquivo: `static/index.html`**
```html
<!DOCTYPE html>
<html>
<head>
    <title>Processamento de Imagens</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        .upload-box { border: 2px dashed #ccc; padding: 20px; margin-bottom: 20px; }
        .resultado { border: 1px solid #ddd; padding: 15px; margin: 10px 0; }
        .label { background: #e3f2fd; padding: 5px; margin: 5px 0; }
        input[type="file"] { padding: 10px; }
        button { padding: 10px 20px; background: #4CAF50; color: white; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Análise de Imagens com Vision API</h1>
        
        <!-- Upload -->
        <div class="upload-box">
            <h2>1. Enviar Imagem</h2>
            <input type="file" id="fileInput" accept="image/*">
            <button onclick="uploadImagem()">Fazer Upload</button>
            <p id="statusUpload"></p>
        </div>
        
        <!-- Resultados -->
        <div>
            <h2>2. Resultados Analisados</h2>
            <button onclick="carregarResultados()">Carregar Resultados</button>
            <div id="resultados"></div>
        </div>
    </div>

    <script>
        // Upload de imagem
        async function uploadImagem() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            
            if (!file) {
                alert('Selecione uma imagem!');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            document.getElementById('statusUpload').textContent = 'Enviando...';
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const dados = await response.json();
                
                if (response.ok) {
                    document.getElementById('statusUpload').textContent = 
                        'Upload realizado! Processando...';
                    
                    // Aguardar alguns segundos e recarregar resultados
                    setTimeout(carregarResultados, 3000);
                } else {
                    document.getElementById('statusUpload').textContent = 
                        'Erro: ' + dados.erro;
                }
            } catch (erro) {
                document.getElementById('statusUpload').textContent = 
                    'Erro de conexão: ' + erro;
            }
        }
        
        // Carregar resultados
        async function carregarResultados() {
            try {
                const response = await fetch('/resultados');
                const resultados = await response.json();
                
                let html = '';
                
                resultados.forEach(resultado => {
                    html += `
                        <div class="resultado">
                            <h3>${resultado.nome_arquivo}</h3>
                            <p><strong>Data:</strong> ${new Date(resultado.data_processamento.seconds * 1000).toLocaleString()}</p>
                            
                            <h4>Rótulos Detectados:</h4>
                            ${resultado.resultados.labels.map(label => 
                                `<div class="label">${label.descricao} (${(label.score * 100).toFixed(1)}%)</div>`
                            ).join('')}
                            
                            <h4>Textos Detectados:</h4>
                            ${resultado.resultados.textos.map(texto => 
                                `<p>${texto.texto}</p>`
                            ).join('') || '<p>Nenhum texto detectado</p>'}
                            
                            <h4>Segurança:</h4>
                            <p>Adulto: ${resultado.resultados.safe_search.adulto}</p>
                            <p>Violência: ${resultado.resultados.safe_search.violencia}</p>
                        </div>
                    `;
                });
                
                document.getElementById('resultados').innerHTML = html;
            } catch (erro) {
                document.getElementById('resultados').innerHTML = 
                    '<p>Erro ao carregar resultados: ' + erro + '</p>';
            }
        }
        
        // Carregar resultados ao abrir página
        window.onload = carregarResultados;
    </script>
</body>
</html>
```

---

## PASSO 4: Configurar Notificações (Opcional - Pub/Sub)

### 4.1 - Criar Tópico Pub/Sub
```bash
gcloud pubsub topics create imagem-processada \
  --project projectcloud-484416
```

### 4.2 - Subscritor de Notificações
**arquivo: `notificacoes.py`**
```python
from google.cloud import pubsub_v1
import json

def subscriber_callback(message):
    """Callback executado quando uma mensagem é recebida"""
    try:
        dados = json.loads(message.data.decode('utf-8'))
        
        print(f"Notificação recebida:")
        print(f"  Arquivo: {dados['nome_arquivo']}")
        print(f"  Documento: {dados['documento_firestore']}")
        print(f"  Labels encontrados: {dados['total_labels']}")
        
        # Aqui você pode enviar email, push notification, webhook, etc.
        # enviar_email_notificacao(email_usuario, dados)
        
        message.ack()
        
    except Exception as e:
        print(f"Erro ao processar notificação: {e}")
        message.nack()

def iniciar_subscriber():
    """Iniciar subscription para ouvir notificações"""
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(
        "projectcloud-484416", 
        "imagem-processada-sub"
    )
    
    streaming_pull_future = subscriber.subscribe(
        subscription_path, 
        callback=subscriber_callback
    )
    
    print("Escutando notificações... (Ctrl+C para sair)")
    
    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        streaming_pull_future.cancel()
        print("Subscriber finalizado")

if __name__ == '__main__':
    iniciar_subscriber()
```

### 4.3 - Criar Subscription
```bash
gcloud pubsub subscriptions create imagem-processada-sub \
  --topic imagem-processada \
  --project projectcloud-484416
```

---

## PASSO 5: Estrutura de Pasta Recomendada

```
projeto_cloud/
│
├── upload_api.py                 # API de upload
├── api_resultados.py             # API de leitura de resultados
├── notificacoes.py               # Subscriber de Pub/Sub
│
├── cloud-function/
│   ├── main.py                   # Código da Cloud Function
│   └── requirements.txt           # Dependências
│
├── static/
│   └── index.html                # Frontend
│
└── README.md                      # Documentação
```

---

## PASSO 6: Variáveis de Ambiente

Criar arquivo `.env`:
```
PROJECT_ID=projectcloud-484416
BUCKET_INPUT=meu-bucket-imagens
BUCKET_OUTPUT=meu-bucket-resultados
PUBSUB_TOPIC=imagem-processada
FIRESTORE_COLLECTION=analises_imagens
```

---

## CHECKLIST DE IMPLEMENTAÇÃO

- [ ] Criar Cloud Storage buckets
- [ ] Configurar permissões IAM
- [ ] Fazer deploy da Cloud Function
- [ ] Criar tópico e subscription Pub/Sub
- [ ] Configurar Firestore
- [ ] Executar API de upload
- [ ] Testar com imagem de exemplo
- [ ] Executar API de resultados
- [ ] Iniciar subscriber de notificações
- [ ] Validar fluxo completo

---

## COMANDOS ÚTEIS

```bash
# Ver logs da Cloud Function
gcloud functions describe processar_imagem --region europe-west1
gcloud functions logs read processar_imagem --region europe-west1 --limit 50

# Ver documentos no Firestore
gcloud firestore documents list --collection-id=analises_imagens

# Testar Pub/Sub
gcloud pubsub subscriptions pull imagem-processada-sub --limit=10
```
