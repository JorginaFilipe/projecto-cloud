"""
Teste Local - Simula Vision API sem precisar de Billing
Útil para desenvolver enquanto aguarda ativação de billing
"""

from flask import Flask, render_template_string, request, jsonify
from google.cloud import firestore
import json
from datetime import datetime
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Usar Firestore apenas (Vision API é simulada localmente)
try:
    db = firestore.Client()
    firestore_disponivel = True
except Exception as e:
    logger.warning(f"Firestore não disponível: {e}")
    firestore_disponivel = False

PROJECT_ID = "projectcloud-484416"

# HTML do Frontend (igual ao anterior)
FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="pt-PT">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análise de Imagens - Teste Local</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        header p {
            opacity: 0.9;
        }
        
        .aviso {
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        
        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .upload-box {
            border: 2px dashed #667eea;
            border-radius: 8px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
        }
        
        input[type="file"] {
            display: none;
        }
        
        .file-input-label {
            cursor: pointer;
            color: #667eea;
            font-weight: bold;
        }
        
        .button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 5px;
            font-size: 1em;
            cursor: pointer;
            margin: 10px 5px;
            font-weight: bold;
        }
        
        .button:hover {
            opacity: 0.9;
        }
        
        .status {
            margin-top: 15px;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
        }
        
        .status.loading {
            background: #fff3cd;
            color: #856404;
        }
        
        .status.success {
            background: #d4edda;
            color: #155724;
        }
        
        .status.error {
            background: #f8d7da;
            color: #721c24;
        }
        
        .resultados-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .resultado-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 8px;
            padding: 15px;
            cursor: pointer;
        }
        
        .resultado-card h3 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .resultado-card .info {
            font-size: 0.9em;
            color: #666;
            margin: 5px 0;
        }
        
        .modal {
            display: none;
            position: fixed;
            z-index: 1;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        
        .modal.show {
            display: block;
        }
        
        .modal-content {
            background-color: #fefefe;
            margin: 5% auto;
            padding: 25px;
            border-radius: 10px;
            width: 90%;
            max-width: 700px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }
        
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover {
            color: #000;
        }
        
        .modal h2 {
            color: #667eea;
            margin-bottom: 15px;
        }
        
        .detalhe {
            background: white;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }
        
        .detalhe strong {
            color: #667eea;
        }
        
        @media (max-width: 768px) {
            .content {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🖼️ Análise de Imagens - Teste Local</h1>
            <p>Simula Vision API localmente (sem billing necessário)</p>
        </header>
        
        <div class="aviso">
            <strong>ℹ️ Modo Teste Local:</strong> Imagens são processadas localmente. 
            Para Vision API real, ative billing em: 
            <a href="https://console.developers.google.com/billing/enable?project=projectcloud-484416" target="_blank" style="color: #856404; text-decoration: underline;">
                Google Cloud Console
            </a>
        </div>
        
        <div class="content">
            <div class="card">
                <h2>1. Enviar Imagem</h2>
                <div class="upload-box">
                    <p style="font-size: 2em; margin-bottom: 10px;">📤</p>
                    <p>Clique para seleccionar imagem</p>
                    <input type="file" id="fileInput" accept="image/*">
                    <label class="file-input-label" for="fileInput">Escolher ficheiro</label>
                </div>
                <div style="text-align: center;">
                    <button class="button" onclick="uploadImagem()">
                        Analisar Imagem
                    </button>
                </div>
                <div id="statusUpload" class="status" style="display: none;"></div>
            </div>
            
            <div class="card">
                <h2>2. Resultados</h2>
                <button class="button" onclick="carregarResultados()">
                    🔄 Carregar Resultados
                </button>
                <div id="contador" style="margin-top: 10px; color: #667eea; font-weight: bold;"></div>
            </div>
        </div>
        
        <div class="card">
            <h2>Análises Realizadas</h2>
            <div id="resultados" class="resultados-grid"></div>
        </div>
    </div>
    
    <div id="detailModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="fecharModal()">&times;</span>
            <h2 id="modalTitle"></h2>
            <div id="modalContent"></div>
        </div>
    </div>

    <script>
        async function uploadImagem() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            const statusDiv = document.getElementById('statusUpload');
            
            if (!file) {
                mostrarStatus(statusDiv, 'Seleccione uma imagem!', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            mostrarStatus(statusDiv, '⏳ Analisando imagem...', 'loading');
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const dados = await response.json();
                
                if (response.ok) {
                    mostrarStatus(statusDiv, '✅ Análise concluída!', 'success');
                    fileInput.value = '';
                    setTimeout(() => carregarResultados(), 1000);
                } else {
                    mostrarStatus(statusDiv, '❌ Erro: ' + dados.erro, 'error');
                }
            } catch (erro) {
                mostrarStatus(statusDiv, '❌ Erro: ' + erro.message, 'error');
            }
        }
        
        async function carregarResultados() {
            try {
                const response = await fetch('/api/resultados');
                const resultados = await response.json();
                
                document.getElementById('contador').textContent = 
                    `Total: ${resultados.length} análise(s)`;
                
                let html = '';
                resultados.forEach(resultado => {
                    const data = new Date(resultado.data_processamento);
                    html += `
                        <div class="resultado-card" onclick="abrirDetalhes(${JSON.stringify(resultado).replace(/"/g, '&quot;')})">
                            <h3>${resultado.nome_arquivo}</h3>
                            <div class="info">📅 ${data.toLocaleDateString('pt-PT')} ${data.toLocaleTimeString('pt-PT')}</div>
                            <div class="info">📊 ${resultado.total_labels} objetos, ${resultado.total_textos} textos</div>
                        </div>
                    `;
                });
                
                document.getElementById('resultados').innerHTML = html || 
                    '<p style="text-align: center; color: #999;">Nenhuma análise realizada</p>';
                
            } catch (erro) {
                console.error('Erro:', erro);
            }
        }
        
        function abrirDetalhes(resultado) {
            const modal = document.getElementById('detailModal');
            document.getElementById('modalTitle').textContent = resultado.nome_arquivo;
            
            let html = `
                <div class="detalhe">
                    <strong>📝 Nome:</strong> ${resultado.nome_arquivo}
                </div>
                <div class="detalhe">
                    <strong>⏰ Data:</strong> ${new Date(resultado.data_processamento).toLocaleString('pt-PT')}
                </div>
                <div class="detalhe">
                    <strong>🏷️ Objetos Detectados (${resultado.total_labels}):</strong><br>
                    ${resultado.resultados.labels.slice(0, 5).map(l => 
                        `${l.descricao} (${(l.score*100).toFixed(0)}%)`
                    ).join('<br>')}
                </div>
                <div class="detalhe">
                    <strong>📄 Textos (${resultado.total_textos}):</strong><br>
                    ${resultado.resultados.texto_completo || 'Nenhum texto detectado'}
                </div>
                <div class="detalhe">
                    <strong>👤 Rostos (${resultado.total_rostos}):</strong><br>
                    ${resultado.total_rostos > 0 ? resultado.total_rostos + ' rosto(s) detectado(s)' : 'Nenhum rosto'}
                </div>
                <div style="margin-top: 15px; padding: 10px; background: #f0f0f0; border-radius: 5px; font-size: 0.9em;">
                    <strong>ℹ️ Nota:</strong> Esta é uma análise simulada localmente. 
                    Para análises reais com Vision API, ative billing.
                </div>
            `;
            
            document.getElementById('modalContent').innerHTML = html;
            modal.classList.add('show');
        }
        
        function fecharModal() {
            document.getElementById('detailModal').classList.remove('show');
        }
        
        function mostrarStatus(div, mensagem, tipo) {
            div.textContent = mensagem;
            div.className = 'status ' + tipo;
            div.style.display = 'block';
        }
        
        window.onclick = function(event) {
            const modal = document.getElementById('detailModal');
            if (event.target === modal) {
                modal.classList.remove('show');
            }
        }
        
        carregarResultados();
    </script>
</body>
</html>
"""


def _processar_imagem_local(imagem_bytes, nome_arquivo):
    """Simula processamento de Vision API localmente"""
    
    # Gerar dados simulados baseados no nome do arquivo
    import hashlib
    hash_obj = hashlib.md5(imagem_bytes)
    hash_val = int(hash_obj.hexdigest(), 16)
    
    # Dados simulados consistentes
    labels_exemplo = [
        "pessoa", "rosto", "interior", "sala", "foto",
        "cor", "luz", "elemento", "objeto", "padrão"
    ]
    
    textos_exemplo = [
        "Olá Mundo",
        "Teste de Análise",
        "Imagem Local",
        "Simulação Vision API",
        ""
    ]
    
    # Seleccionar baseado no hash
    idx_label = hash_val % len(labels_exemplo)
    idx_texto = (hash_val // len(labels_exemplo)) % len(textos_exemplo)
    
    resultados = {
        'labels': [
            {'descricao': labels_exemplo[i], 'score': 0.5 + (i * 0.04)}
            for i in range(min(5, len(labels_exemplo)))
        ],
        'texto_completo': textos_exemplo[idx_texto],
        'textos': [],
        'rostos': [
            {'confianca': 0.85, 'alegria': 7}
        ] if hash_val % 3 == 0 else [],
        'safe_search': {
            'adulto': 'UNLIKELY',
            'violencia': 'UNLIKELY',
            'spoof': 'UNLIKELY',
            'medical': 'UNLIKELY',
            'racy': 'UNLIKELY'
        },
        'cores_dominantes': [
            {'cor_rgb': {'red': 100, 'green': 150, 'blue': 200}, 'pixel_fraction': 0.3},
            {'cor_rgb': {'red': 200, 'green': 100, 'blue': 50}, 'pixel_fraction': 0.25}
        ]
    }
    
    return resultados


@app.route('/')
def index():
    """Servir frontend"""
    return render_template_string(FRONTEND_HTML)


@app.route('/upload', methods=['POST'])
def upload_imagem():
    """Upload e processamento local"""
    try:
        if 'file' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'erro': 'Nome vazio'}), 400
        
        logger.info(f"Processando: {file.filename}")
        
        # Ler arquivo
        imagem_bytes = file.read()
        
        # Processar localmente
        resultados = _processar_imagem_local(imagem_bytes, file.filename)
        
        # Guardar no Firestore (se disponível)
        doc_id = None
        if firestore_disponivel:
            try:
                dados = {
                    'nome_arquivo': file.filename,
                    'data_processamento': datetime.now(),
                    'status': 'processado',
                    'total_labels': len(resultados.get('labels', [])),
                    'total_textos': len(resultados.get('textos', [])),
                    'total_rostos': len(resultados.get('rostos', [])),
                    'resultados': resultados
                }
                _, doc_ref = db.collection('analises_imagens').add(dados)
                doc_id = doc_ref.id
            except Exception as e:
                logger.warning(f"Firestore indisponível: {e}")
        
        logger.info(f"Processado: {doc_id or 'sem guardar'}")
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Imagem analisada localmente',
            'documento_id': doc_id
        }), 200
        
    except Exception as e:
        logger.error(f"Erro: {str(e)}")
        return jsonify({'erro': str(e)}), 500


@app.route('/api/resultados', methods=['GET'])
def api_resultados():
    """Obter resultados"""
    try:
        if not firestore_disponivel:
            return jsonify([]), 200
        
        docs = db.collection('analises_imagens').order_by(
            'data_processamento',
            direction=firestore.Query.DESCENDING
        ).limit(50).stream()
        
        resultados = []
        for doc in docs:
            resultado = doc.to_dict()
            resultado['id'] = doc.id
            resultado['data_processamento'] = resultado['data_processamento'].isoformat()
            resultados.append(resultado)
        
        return jsonify(resultados), 200
        
    except Exception as e:
        logger.error(f"Erro: {str(e)}")
        return jsonify([]), 200


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🧪 TESTE LOCAL - Análise de Imagens")
    print("="*60)
    print("\n✅ Abra: http://localhost:5000")
    print("\nℹ️  Modo Local (sem Vision API real)")
    print("\nPara Vision API real, ative billing em:")
    print("   https://console.developers.google.com/billing/enable")
    print("\nPressione Ctrl+C para parar\n")
    
    app.run(debug=True, port=5000, host='127.0.0.1')
