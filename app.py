"""
Aplicação Flask Integrada - Processamento de Imagens com Google Cloud Vision
Uma aplicação completa que:
- Serve o frontend web
- Recebe uploads de imagens
- Processa com Vision API
- Armazena em Firestore
- Mostra resultados em tempo real
"""

from flask import Flask, render_template_string, request, jsonify, send_file
from google.cloud import storage
from google.cloud import vision
from google.cloud import firestore
from google.cloud import pubsub_v1
import json
import os
from datetime import datetime
import logging
from io import BytesIO
import base64

# Configuração de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar Flask
app = Flask(__name__)

# Inicializar clientes Google Cloud
storage_client = storage.Client()
vision_client = vision.ImageAnnotatorClient()
db = firestore.Client()
publisher_client = pubsub_v1.PublisherClient()

# Configurações
PROJECT_ID = "projectcloud-484416"
BUCKET_NAME = "meu-bucket-imagens"
PUBSUB_TOPIC = "imagem-processada"

# HTML do Frontend (embutido)
FRONTEND_HTML = """
<!DOCTYPE html>
<html lang="pt-PT">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análise de Imagens - Vision API</title>
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
            transition: background 0.3s;
        }
        
        .upload-box:hover {
            background: #f5f5f5;
        }
        
        .upload-box.dragover {
            background: #f0f0ff;
            border-color: #764ba2;
        }
        
        input[type="file"] {
            display: none;
        }
        
        .file-input-label {
            cursor: pointer;
            color: #667eea;
            font-weight: bold;
            font-size: 1.1em;
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
        
        .button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
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
            position: relative;
            transition: transform 0.3s;
        }
        
        .resultado-card:hover {
            transform: scale(1.02);
        }
        
        .resultado-card h3 {
            color: #667eea;
            word-break: break-word;
            font-size: 0.95em;
            padding-right: 80px;
        }
        
        .card-actions {
            position: absolute;
            top: 10px;
            right: 10px;
            display: flex;
            gap: 5px;
        }
        
        .btn-icon {
            background: white;
            border: none;
            width: 35px;
            height: 35px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2em;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: background 0.3s;
        }
        
        .btn-icon:hover {
            background: #f0f0f0;
        }
        
        .btn-delete:hover {
            background: #ffebee;
            color: #c62828;
        }
        
        .resultado-card .data {
            font-size: 0.85em;
            color: #666;
            margin: 8px 0;
        }
        
        .stats {
            display: flex;
            justify-content: space-around;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
        }
        
        .stat-number {
            font-size: 1.3em;
            font-weight: bold;
            color: #667eea;
            text-align: center;
        }
        
        .stat-label {
            font-size: 0.8em;
            color: #666;
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
            overflow: auto;
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
            max-height: 80vh;
            overflow-y: auto;
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
        
        .detail-section {
            margin: 20px 0;
            padding: 15px;
            background: #f9f9f9;
            border-radius: 5px;
        }
        
        .detail-section h3 {
            color: #764ba2;
            margin-bottom: 10px;
        }
        
        .label-item {
            background: white;
            padding: 10px;
            margin: 8px 0;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }
        
        .label-item .score {
            float: right;
            background: #667eea;
            color: white;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: bold;
        }
        
        .color-box {
            display: inline-block;
            width: 30px;
            height: 30px;
            border-radius: 5px;
            margin-right: 10px;
            vertical-align: middle;
        }
        
        .tabs {
            display: flex;
            border-bottom: 2px solid #ddd;
            margin-bottom: 15px;
        }
        
        .tab-button {
            padding: 10px 20px;
            background: none;
            border: none;
            cursor: pointer;
            color: #667eea;
            font-weight: bold;
            border-bottom: 3px solid transparent;
        }
        
        .tab-button.active {
            border-bottom-color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        @media (max-width: 768px) {
            .content {
                grid-template-columns: 1fr;
            }
            
            .resultados-grid {
                grid-template-columns: 1fr;
            }
            
            header h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Análise de Imagens</h1>            
            <p>Universidade Autónoma de Lisboa</p>
        </header>
        
        <div class="content">
            <div class="card">
                <h2>1. Enviar Imagem</h2>
                <div class="upload-box" id="dropZone">
                    <p style="font-size: 2em; margin-bottom: 10px;">📤</p>
                    <p>Clique ou arraste uma imagem aqui</p>
                    <input type="file" id="fileInput" accept="image/*">
                    <label class="file-input-label" for="fileInput">Seleccionar ficheiro</label>
                </div>
                <div style="text-align: center;">
                    <button class="button" onclick="uploadImagem()" id="uploadBtn">
                        Fazer Upload
                    </button>
                </div>
                <div id="statusUpload" class="status" style="display: none;"></div>
            </div>
            
            <div class="card">
                <h2>2. Resultados Recentes</h2>
                <button class="button" onclick="carregarResultados()">
                    🔄 Carregar Resultados
                </button>
                <button class="button" style="background: #dc3545; margin-top: 10px;" onclick="limparTudo()">
                    🗑️ Limpar Tudo
                </button>
                <div id="contadorResultados" style="margin-top: 10px; color: #667eea; font-weight: bold;"></div>
            </div>
        </div>
        
        <div class="card">
            <h2>Análises Realizadas</h2>
            <div id="resultados" class="resultados-grid"></div>
        </div>
    </div>
    
    <!-- Modal de Detalhes -->
    <div id="detailModal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="fecharModal()">&times;</span>
            <h2 id="modalTitle"></h2>
            
            <div class="tabs">
                <button class="tab-button active" onclick="mostrarTab(event, 'labels')">Objetos</button>
                <button class="tab-button" onclick="mostrarTab(event, 'textos')">Texto</button>
                <button class="tab-button" onclick="mostrarTab(event, 'rostos')">Rostos</button>
                <button class="tab-button" onclick="mostrarTab(event, 'cores')">Cores</button>
                <button class="tab-button" onclick="mostrarTab(event, 'seguranca')">Segurança</button>
            </div>
            
            <div id="labels" class="tab-content active">
                <div class="detail-section" id="labelsContent"></div>
            </div>
            
            <div id="textos" class="tab-content">
                <div class="detail-section" id="textosContent"></div>
            </div>
            
            <div id="rostos" class="tab-content">
                <div class="detail-section" id="rostosContent"></div>
            </div>
            
            <div id="cores" class="tab-content">
                <div class="detail-section" id="coresContent"></div>
            </div>
            
            <div id="seguranca" class="tab-content">
                <div class="detail-section" id="segurancaContent"></div>
            </div>
        </div>
    </div>

    <!-- Modal de Visualizar Imagem -->
    <div id="imageModal" class="modal">
        <div class="modal-content" style="text-align: center; max-width: 900px;">
            <span class="close" onclick="fecharImageModal()">&times;</span>
            <h2 id="imageTitle"></h2>
            <img id="imagePreview" src="" alt="Preview" style="max-width: 100%; max-height: 600px; border-radius: 8px; margin: 20px 0;">
            <div style="margin-top: 20px;">
                <button class="button" onclick="deletarImagem()">🗑️ Eliminar Imagem</button>
                <button class="button" onclick="fecharImageModal()" style="background: #999;">Fechar</button>
            </div>
        </div>
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        
        // Dicionário de tradução de labels
        const dicionarioLabels = {
            // Partes do corpo
            'eyebrow': 'Sobrancelha',
            'eyebrows': 'Sobrancelhas',
            'lips': 'Lábios',
            'hair': 'Cabelo',
            'black hair': 'Cabelo preto',
            'blond hair': 'Cabelo louro',
            'blonde': 'Louro(a)',
            'blond': 'Louro(a)',
            'blonds': 'Louros(as)',
            'eyelash': 'Cílio',
            'eyelashes': 'Cílios',
            'nose': 'Nariz',
            'eyes': 'Olhos',
            'eye': 'Olho',
            'mouth': 'Boca',
            'chin': 'Queixo',
            'forehead': 'Testa',
            'cheek': 'Bochecha',
            'cheeks': 'Bochechas',
            'skin': 'Pele',
            'thigh': 'Coxa',
            'thighs': 'Coxas',
            'leg': 'Perna',
            'legs': 'Pernas',
            'arm': 'Braço',
            'arms': 'Braços',
            'hand': 'Mão',
            'hands': 'Mãos',
            'shoulder': 'Ombro',
            'shoulders': 'Ombros',
            'back': 'Costas',
            'chest': 'Peito',
            'waist': 'Cintura',
            'belly': 'Barriga',
            'foot': 'Pé',
            'feet': 'Pés',
            
            // Características e expressões
            'facial expression': 'Expressão facial',
            'smile': 'Sorriso',
            'beauty': 'Beleza',
            'lipstick': 'Batom',
            'makeup': 'Maquilhagem',
            'eyeshadow': 'Sombra de olhos',
            'blush': 'Rubor',
            'long hair': 'Cabelo comprido',
            'long hairs': 'Cabelos compridos',
            'short hair': 'Cabelo curto',
            'short hairs': 'Cabelos curtos',
            'curly hair': 'Cabelo caracol',
            'straight hair': 'Cabelo liso',
            'wavy hair': 'Cabelo ondulado',
            
            // Penteados
            'cornrows': 'Tranças',
            'dreadlocks': 'Tranças de Rastafári',
            'braids': 'Tranças',
            'braid': 'Trança',
            'buzz cut': 'Corte de cabelo curto',
            'ponytail': 'Rabo de cavalo',
            'bun': 'Coque',
            'mohawk': 'Penteado Mohawk',
            
            // Roupa e acessórios
            'bra': 'Sutiã',
            'bras': 'Sutiãs',
            'lingerie': 'Roupa interior',
            'lingeries': 'Roupas interiores',
            'undergarment': 'Peça de roupa interior',
            'undergarments': 'Peças de roupa interior',
            'bikini': 'Biquíni',
            'bikinis': 'Biquínis',
            'swimsuit': 'Fato de banho',
            'dress': 'Vestido',
            'shirt': 'Camisa',
            'pants': 'Calças',
            'jeans': 'Calças de ganga',
            'skirt': 'Saia',
            'jacket': 'Casaco',
            'coat': 'Sobretudo',
            'hat': 'Chapéu',
            'cap': 'Boné',
            'glasses': 'Óculos',
            'sunglasses': 'Óculos de sol',
            'necklace': 'Colar',
            'bracelet': 'Pulseira',
            'ring': 'Anel',
            'earring': 'Brinco',
            'earrings': 'Brincos',
            'watch': 'Relógio',
            'shoe': 'Sapato',
            'shoes': 'Sapatos',
            'boot': 'Bota',
            'boots': 'Botas',
            'tie': 'Gravata',
            'scarf': 'Lenço',
            'belt': 'Cinto',
            
            // Fotografia
            'portrait photography': 'Fotografia de retrato',
            'portrait': 'Retrato',
            'photograph': 'Fotografia',
            'photography': 'Fotografia',
            'close-up': 'Plano aproximado',
            'headshot': 'Fotografia de cabeça',
            'selfie': 'Selfie',
            'model': 'Modelo',
            'art model': 'Modelo de arte',
            'fashion model': 'Modelo de moda',
            
            // Tipos de corpo
            'muscular': 'Musculado(a)',
            'slim': 'Magro(a)',
            'curvy': 'Com curvas',
            'athletic': 'Atlético(a)',
            
            // Gênero
            'woman': 'Mulher',
            'man': 'Homem',
            'girl': 'Miúda',
            'boy': 'Miúdo',
            'female': 'Feminino',
            'male': 'Masculino',
            'person': 'Pessoa',
            'people': 'Pessoas',
            
            // Etnias/Origem (tradução neutra)
            'african': 'Africano(a)',
            'asian': 'Asiático(a)',
            'caucasian': 'Caucasiano(a)',
            'indian': 'Indiano(a)',
            'latino': 'Latino(a)',
            
            // Outras características
            'young': 'Jovem',
            'old': 'Idoso(a)',
            'adult': 'Adulto(a)',
            'child': 'Criança',
            'baby': 'Bebé',
            'senior': 'Idoso(a)',
            'elderly': 'Idoso(a)',
            'teenager': 'Adolescente',
            
            // Móvel e objetos
            'furniture': 'Móvel',
            'chair': 'Cadeira',
            'table': 'Mesa',
            'bed': 'Cama',
            'sofa': 'Sofá',
            'couch': 'Sofá',
            'desk': 'Secretária',
            'lamp': 'Lâmpada',
            'mirror': 'Espelho',
            'wall': 'Parede',
            'floor': 'Chão',
            'ceiling': 'Teto',
            'door': 'Porta',
            'window': 'Janela',
            'curtain': 'Cortina',
            'document': 'Documento',
            'identity document': 'Documento de identidade',
            'mobile phone': 'Telemóvel',
            'phone': 'Telemóvel',
            'smartphone': 'Smartphone',
            'camera': 'Câmara',
            'computer': 'Computador',
            'keyboard': 'Teclado',
            'mouse': 'Rato',
            
            // Arte e design
            'art': 'Arte',
            'design': 'Design',
            'graphic design': 'Design gráfico',
            'graphics': 'Gráficos',
            'fashion': 'Moda',
            
            // Cores
            'red': 'Vermelho',
            'blue': 'Azul',
            'green': 'Verde',
            'yellow': 'Amarelo',
            'orange': 'Laranja',
            'pink': 'Rosa',
            'purple': 'Roxo',
            'black': 'Preto',
            'white': 'Branco',
            'gray': 'Cinzento',
            'grey': 'Cinzento',
            'brown': 'Castanho',
            'gold': 'Ouro',
            'silver': 'Prata',
            'cyan': 'Ciano',
            'magenta': 'Magenta'
        };
        
        // Função para traduzir labels
        function traduzirLabel(label) {
            const labelMinuscula = label.toLowerCase();
            return dicionarioLabels[labelMinuscula] || label;
        }
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                document.getElementById('fileInput').files = files;
            }
        });
        
        async function uploadImagem() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            const statusDiv = document.getElementById('statusUpload');
            const uploadBtn = document.getElementById('uploadBtn');
            
            if (!file) {
                mostrarStatus(statusDiv, 'Seleccione uma imagem!', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            mostrarStatus(statusDiv, '⏳ Enviando e processando...', 'loading');
            uploadBtn.disabled = true;
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const dados = await response.json();
                
                if (response.ok) {
                    mostrarStatus(statusDiv, '✅ Processamento concluído! Atualizando...', 'success');
                    fileInput.value = '';
                    setTimeout(() => carregarResultados(), 1000);
                } else {
                    mostrarStatus(statusDiv, '❌ Erro: ' + dados.erro, 'error');
                }
            } catch (erro) {
                mostrarStatus(statusDiv, '❌ Erro: ' + erro.message, 'error');
            } finally {
                uploadBtn.disabled = false;
            }
        }
        
        async function carregarResultados() {
            try {
                const response = await fetch('/api/resultados');
                const resultados = await response.json();
                
                const contador = document.getElementById('contadorResultados');
                contador.textContent = `Total: ${resultados.length} análise(s)`;
                
                let html = '';
                
                resultados.forEach(resultado => {
                    const data = new Date(resultado.data_processamento);
                    const dataFormatada = data.toLocaleDateString('pt-PT') + ' ' + 
                                         data.toLocaleTimeString('pt-PT', {hour: '2-digit', minute:'2-digit'});
                    
                    html += `
                        <div class="resultado-card">
                            <div class="card-actions">
                                <button class="btn-icon" onclick="abrirImagemModal('${resultado.id}', '${resultado.nome_arquivo}'); event.stopPropagation();" title="Visualizar imagem">
                                    👁️
                                </button>
                            </div>
                            <div onclick="abrirDetalhes('${resultado.id}', ${JSON.stringify(resultado).replace(/"/g, '&quot;')})">
                                <h3>${resultado.nome_arquivo}</h3>
                                <div class="data">📅 ${dataFormatada}</div>
                                <div class="stats">
                                    <div>
                                        <div class="stat-number">${resultado.total_labels}</div>
                                        <div class="stat-label">Objetos</div>
                                    </div>
                                    <div>
                                        <div class="stat-number">${resultado.total_textos}</div>
                                        <div class="stat-label">Textos</div>
                                    </div>
                                    <div>
                                        <div class="stat-number">${resultado.total_rostos}</div>
                                        <div class="stat-label">Rostos</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                document.getElementById('resultados').innerHTML = html || '<p style="text-align: center; color: #999;">Nenhuma análise realizada ainda.</p>';
            } catch (erro) {
                console.error('Erro:', erro);
            }
        }
        
        function abrirDetalhes(docId, resultado) {
            const modal = document.getElementById('detailModal');
            document.getElementById('modalTitle').textContent = resultado.nome_arquivo;
            
            // Labels
            const labelsHtml = resultado.resultados.labels
                .sort((a, b) => b.score - a.score)
                .slice(0, 10)
                .map(label => `
                    <div class="label-item">
                        <strong>${traduzirLabel(label.descricao)}</strong>
                        <span class="score">${(label.score * 100).toFixed(1)}%</span>
                    </div>
                `).join('');
            document.getElementById('labelsContent').innerHTML = labelsHtml || '<p>Nenhum objeto detectado.</p>';
            
            // Textos
            const textoCompleto = resultado.resultados.texto_completo || 'Nenhum texto detectado.';
            const textosHtml = `
                <h3>Texto Completo</h3>
                <p>${textoCompleto}</p>
            `;
            document.getElementById('textosContent').innerHTML = textosHtml;
            
            // Rostos
            const rostosHtml = resultado.resultados.rostos.length > 0 ?
                resultado.resultados.rostos.map((rosto, i) => `
                    <div style="margin: 10px 0; padding: 10px; background: white; border-radius: 5px;">
                        <strong>Rosto ${i + 1}</strong>
                        <p>Confiança: ${(rosto.confianca * 100).toFixed(1)}%</p>
                        <p>Alegria: ${rosto.alegria}/10</p>
                    </div>
                `).join('') : '<p>Nenhum rosto detectado.</p>';
            document.getElementById('rostosContent').innerHTML = rostosHtml;
            
            // Cores
            const coresHtml = resultado.resultados.cores_dominantes ?
                resultado.resultados.cores_dominantes.map(cor => `
                    <div style="margin: 10px 0; display: flex; align-items: center;">
                        <div class="color-box" style="background: rgb(${cor.cor_rgb.red}, ${cor.cor_rgb.green}, ${cor.cor_rgb.blue});"></div>
                        <span>rgb(${cor.cor_rgb.red}, ${cor.cor_rgb.green}, ${cor.cor_rgb.blue}) - ${(cor.pixel_fraction * 100).toFixed(1)}%</span>
                    </div>
                `).join('') : '<p>Nenhuma cor detectada.</p>';
            document.getElementById('coresContent').innerHTML = coresHtml;
            
            // Segurança
            const seguranca = resultado.resultados.safe_search;
            
            // Função para traduzir likelihood
            function traduzirLikelihood(valor) {
                const mapa = {
                    'Likelihood.VERY_UNLIKELY': 'Muito Improvável',
                    'Likelihood.UNLIKELY': 'Improvável',
                    'Likelihood.POSSIBLE': 'Possível',
                    'Likelihood.LIKELY': 'Provável',
                    'Likelihood.VERY_LIKELY': 'Muito Provável',
                    'VERY_UNLIKELY': 'Muito Improvável',
                    'UNLIKELY': 'Improvável',
                    'POSSIBLE': 'Possível',
                    'LIKELY': 'Provável',
                    'VERY_LIKELY': 'Muito Provável'
                };
                return mapa[valor] || valor;
            }
            
            const segurancaHtml = `
                <p><strong>Conteúdo Adulto:</strong> ${traduzirLikelihood(seguranca.adulto)}</p>
                <p><strong>Violência:</strong> ${traduzirLikelihood(seguranca.violencia)}</p>
                <p><strong>Falsificação (Spoof):</strong> ${traduzirLikelihood(seguranca.spoof)}</p>
                <p><strong>Conteúdo Médico:</strong> ${traduzirLikelihood(seguranca.medical)}</p>
                <p><strong>Conteúdo Adulto Implícito:</strong> ${traduzirLikelihood(seguranca.racy)}</p>
            `;
            document.getElementById('segurancaContent').innerHTML = segurancaHtml;
            
            modal.classList.add('show');
        }
        
        function fecharModal() {
            document.getElementById('detailModal').classList.remove('show');
        }
        
        function fecharImageModal() {
            document.getElementById('imageModal').classList.remove('show');
        }
        
        async function abrirImagemModal(docId, nomeArquivo) {
            try {
                const response = await fetch(`/api/imagem/${docId}`);
                const data = await response.json();
                
                if (response.ok && data.imagem_base64) {
                    document.getElementById('imageTitle').textContent = nomeArquivo;
                    document.getElementById('imagePreview').src = 'data:image/jpeg;base64,' + data.imagem_base64;
                    document.getElementById('imageModal').classList.add('show');
                    currentImageId = docId;
                } else {
                    alert('Erro ao carregar imagem.');
                }
            } catch (erro) {
                alert('Erro: ' + erro.message);
            }
        }
        
        async function deletarImagem() {
            if (!confirm('Tem a certeza que deseja eliminar esta imagem e seus dados?')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/imagem/${currentImageId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    alert('✅ Imagem eliminada com sucesso.');
                    fecharImageModal();
                    carregarResultados();
                } else {
                    alert('❌ Erro ao eliminar imagem.');
                }
            } catch (erro) {
                alert('Erro: ' + erro.message);
            }
        }
        
        let currentImageId = null;
        
        function mostrarTab(event, tabName) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        function mostrarStatus(div, mensagem, tipo) {
            div.textContent = mensagem;
            div.className = 'status ' + tipo;
            div.style.display = 'block';
        }
        
        async function limparTudo() {
            const confirmacao = confirm('⚠️ Tem a certeza?\\n\\nIsso irá ELIMINAR TODAS as imagens e dados armazenados permanentemente!\\n\\nEsta ação NÃO pode ser desfeita.');
            
            if (!confirmacao) {
                return;
            }
            
            try {
                const response = await fetch('/api/limpar-tudo', {
                    method: 'POST'
                });
                
                const dados = await response.json();
                
                if (response.ok) {
                    alert(`✅ Base de dados limpa!\\n\\n${dados.total} imagens foram eliminadas.`);
                    carregarResultados();
                } else {
                    alert('❌ Erro: ' + dados.erro);
                }
            } catch (erro) {
                alert('❌ Erro ao limpar: ' + erro.message);
            }
        }
        
        window.onclick = function(event) {
            const modal = document.getElementById('detailModal');
            const imageModal = document.getElementById('imageModal');
            if (event.target === modal) {
                modal.classList.remove('show');
            }
            if (event.target === imageModal) {
                imageModal.classList.remove('show');
            }
        }
        
        carregarResultados();
    </script>
</body>
</html>
"""


# ============================================================================
# ROTAS
# ============================================================================

@app.route('/')
def index():
    """Servir o frontend HTML"""
    return render_template_string(FRONTEND_HTML)


@app.route('/upload', methods=['POST'])
def upload_imagem():
    """Upload e processamento de imagem"""
    try:
        if 'file' not in request.files:
            return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'erro': 'Nome de arquivo vazio'}), 400
        
        # Validar tipo
        allowed = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed:
            return jsonify({'erro': 'Tipo de arquivo não permitido'}), 400
        
        logger.info(f"Processando upload: {file.filename}")
        
        # Ler arquivo em memória
        imagem_bytes = file.read()
        
        # Processar com Vision API
        resultados = _processar_imagem(imagem_bytes)
        
        # Guardar no Firestore
        doc_id = _guardar_firestore(file.filename, resultados, imagem_bytes)
        
        # Publicar notificação
        _publicar_notificacao(file.filename, doc_id, resultados)
        
        logger.info(f"Imagem processada com sucesso: {doc_id}")
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Imagem processada com sucesso',
            'documento_id': doc_id
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao processar: {str(e)}")
        return jsonify({'erro': str(e)}), 500


@app.route('/api/resultados', methods=['GET'])
def api_resultados():
    """Obter todos os resultados"""
    try:
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
        logger.error(f"Erro ao listar: {str(e)}")
        return jsonify({'erro': str(e)}), 500


@app.route('/api/imagem/<doc_id>', methods=['GET'])
def api_imagem(doc_id):
    """Obter a imagem em base64"""
    try:
        doc = db.collection('analises_imagens').document(doc_id).get()
        if not doc.exists:
            return jsonify({'erro': 'Imagem não encontrada'}), 404
        
        dados = doc.to_dict()
        imagem_base64 = dados.get('imagem_base64', '')
        
        return jsonify({'imagem_base64': imagem_base64}), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter imagem: {str(e)}")
        return jsonify({'erro': str(e)}), 500


@app.route('/api/imagem/<doc_id>', methods=['DELETE'])
def deletar_imagem(doc_id):
    """Eliminar uma imagem e seus dados"""
    try:
        db.collection('analises_imagens').document(doc_id).delete()
        logger.info(f"Imagem eliminada: {doc_id}")
        return jsonify({'sucesso': True, 'mensagem': 'Imagem eliminada'}), 200
        
    except Exception as e:
        logger.error(f"Erro ao eliminar: {str(e)}")
        return jsonify({'erro': str(e)}), 500


@app.route('/api/limpar-tudo', methods=['POST'])
def limpar_tudo():
    """Eliminar TODAS as imagens e dados da base de dados"""
    try:
        # Obter todas as imagens
        docs = db.collection('analises_imagens').stream()
        
        contador = 0
        for doc in docs:
            doc.reference.delete()
            contador += 1
        
        logger.info(f"Base de dados limpa: {contador} imagens eliminadas")
        return jsonify({'sucesso': True, 'mensagem': f'{contador} imagens eliminadas', 'total': contador}), 200
        
    except Exception as e:
        logger.error(f"Erro ao limpar base de dados: {str(e)}")
        return jsonify({'erro': str(e)}), 500


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def _processar_imagem(imagem_bytes):
    """Processar imagem com Vision API"""
    logger.info("Iniciando análise com Vision API...")
    
    image = vision.Image(content=imagem_bytes)
    resultados = {}
    
    try:
        # 1. Labels
        logger.info("Label Detection...")
        response = vision_client.label_detection(image=image)
        resultados['labels'] = [
            {'descricao': label.description, 'score': float(label.score)}
            for label in response.label_annotations
        ]
        
        # 2. Text Detection
        logger.info("Text Detection...")
        response = vision_client.text_detection(image=image)
        if response.text_annotations:
            resultados['texto_completo'] = response.text_annotations[0].description if response.text_annotations else ""
            resultados['textos'] = []
        else:
            resultados['texto_completo'] = ""
            resultados['textos'] = []
        
        # 3. Face Detection
        logger.info("Face Detection...")
        response = vision_client.face_detection(image=image)
        resultados['rostos'] = [
            {
                'confianca': float(face.detection_confidence),
                'alegria': int(face.joy_likelihood),
                'surpresa': int(face.surprise_likelihood)
            }
            for face in response.face_annotations
        ]
        
        # 4. Safe Search
        logger.info("Safe Search Detection...")
        response = vision_client.safe_search_detection(image=image)
        resultados['safe_search'] = {
            'adulto': str(response.safe_search_annotation.adult),
            'violencia': str(response.safe_search_annotation.violence),
            'spoof': str(response.safe_search_annotation.spoof),
            'medical': str(response.safe_search_annotation.medical),
            'racy': str(response.safe_search_annotation.racy)
        }
        
        # 5. Colors
        logger.info("Image Properties...")
        try:
            response = vision_client.image_properties(image=image)
            resultados['cores_dominantes'] = [
                {
                    'cor_rgb': {
                        'red': int(color.color.red),
                        'green': int(color.color.green),
                        'blue': int(color.color.blue)
                    },
                    'score': float(color.score),
                    'pixel_fraction': float(color.pixel_fraction)
                }
                for color in response.dominant_colors.colors
            ]
        except Exception as e:
            logger.warning(f"Erro ao processar cores: {e}")
            resultados['cores_dominantes'] = []
        
        logger.info("Análise concluída com sucesso")
        return resultados
        
    except Exception as e:
        logger.error(f"Erro na análise: {str(e)}")
        raise


def _guardar_firestore(nome_arquivo, resultados, imagem_bytes):
    """Guardar resultados no Firestore"""
    logger.info("Guardando no Firestore...")
    
    # Converter imagem para base64
    import base64
    imagem_base64 = base64.b64encode(imagem_bytes).decode('utf-8')
    
    dados = {
        'nome_arquivo': nome_arquivo,
        'data_processamento': datetime.now(),
        'status': 'processado',
        'total_labels': len(resultados.get('labels', [])),
        'total_textos': len(resultados.get('textos', [])),
        'total_rostos': len(resultados.get('rostos', [])),
        'resultados': resultados,
        'imagem_base64': imagem_base64
    }
    
    _, doc_ref = db.collection('analises_imagens').add(dados)
    logger.info(f"Documento criado: {doc_ref.id}")
    return doc_ref.id


def _publicar_notificacao(nome_arquivo, doc_id, resultados):
    """Publicar em Pub/Sub"""
    try:
        logger.info("Publicando notificação...")
        topic_path = publisher_client.topic_path(PROJECT_ID, PUBSUB_TOPIC)
        
        mensagem = {
            'arquivo': nome_arquivo,
            'documento': doc_id,
            'timestamp': datetime.now().isoformat(),
            'labels': len(resultados.get('labels', []))
        }
        
        publisher_client.publish(topic_path, json.dumps(mensagem).encode('utf-8'))
        logger.info("Notificação publicada")
        
    except Exception as e:
        logger.warning(f"Erro ao publicar: {str(e)}")


# ============================================================================
# EXECUTAR APP
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Aplicação de Análise de Imagens")
    print("="*60)
    print("\n✅ Frontend:  http://localhost:5000")
    print("✅ API:       http://localhost:5000/api/resultados")
    print("\nPressione Ctrl+C para parar\n")
    
    app.run(debug=True, port=5000, host='127.0.0.1')
