"""
API para Upload de Imagens para Google Cloud Storage
"""
from flask import Flask, request, jsonify
from google.cloud import storage
from datetime import datetime
import os

app = Flask(__name__)

# Configuração
BUCKET_NAME = "meu-bucket-imagens"
INPUT_FOLDER = "input/"
PROJECT_ID = "projectcloud-484416"

# Inicializar cliente do Storage
storage_client = storage.Client(project=PROJECT_ID)
bucket = storage_client.bucket(BUCKET_NAME)


@app.route('/upload', methods=['POST'])
def upload_imagem():
    """
    Endpoint para upload de imagem
    Esperado: arquivo em multipart/form-data
    
    Exemplo com curl:
    curl -X POST -F "file=@imagem.jpg" http://localhost:5000/upload
    """
    try:
        # Validar se arquivo foi enviado
        if 'file' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'erro': 'Nome de arquivo vazio'}), 400
        
        # Validar tipo de arquivo
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if ext not in allowed_extensions:
            return jsonify({'erro': f'Tipo de arquivo não permitido. Use: {allowed_extensions}'}), 400
        
        # Gerar nome único com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = f"{INPUT_FOLDER}{timestamp}_{file.filename}"
        
        # Fazer upload para Cloud Storage
        blob = bucket.blob(nome_arquivo)
        blob.upload_from_file(file, content_type=file.content_type)
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'Imagem {file.filename} enviada com sucesso',
            'blob_path': nome_arquivo,
            'bucket': BUCKET_NAME,
            'timestamp': timestamp
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint com instruções"""
    return jsonify({
        'api': 'Upload de Imagens - Google Cloud',
        'endpoints': {
            'POST /upload': 'Fazer upload de imagem (multipart/form-data)',
            'GET /health': 'Verificar status da API'
        }
    }), 200


if __name__ == '__main__':
    print(f"Iniciando API de Upload...")
    print(f"Bucket: {BUCKET_NAME}")
    print(f"Projeto: {PROJECT_ID}")
    app.run(debug=True, port=5000)
