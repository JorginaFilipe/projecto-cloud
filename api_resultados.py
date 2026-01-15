"""
API para Consultar Resultados das Análises no Firestore
"""
from flask import Flask, jsonify, request
from google.cloud import firestore
from datetime import datetime
import logging

app = Flask(__name__)
db = firestore.Client()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "projectcloud-484416"


@app.route('/resultados/<doc_id>', methods=['GET'])
def obter_resultado(doc_id):
    """Obter resultado de uma análise específica"""
    try:
        logger.info(f"Consultando resultado: {doc_id}")
        
        doc = db.collection('analises_imagens').document(doc_id).get()
        
        if not doc.exists:
            return jsonify({'erro': 'Documento não encontrado'}), 404
        
        resultado = doc.to_dict()
        resultado['id'] = doc_id
        
        # Converter timestamps para string
        if 'data_processamento' in resultado:
            resultado['data_processamento'] = resultado['data_processamento'].isoformat()
        
        return jsonify(resultado), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter resultado: {str(e)}")
        return jsonify({'erro': str(e)}), 500


@app.route('/resultados', methods=['GET'])
def listar_resultados():
    """
    Listar todas as análises realizadas
    Parâmetros opcionais:
    - limit: número de resultados (padrão: 20, máximo: 100)
    - offset: número de resultados a pular (para paginação)
    """
    try:
        limit = min(int(request.args.get('limit', 20)), 100)
        offset = int(request.args.get('offset', 0))
        
        logger.info(f"Listando resultados - limit: {limit}, offset: {offset}")
        
        query = db.collection('analises_imagens').order_by(
            'data_processamento', 
            direction=firestore.Query.DESCENDING
        )
        
        # Aplicar limit
        docs = query.limit(limit + offset).stream()
        
        resultados = []
        for i, doc in enumerate(docs):
            if i < offset:  # Pular os offset primeiros
                continue
            
            resultado = doc.to_dict()
            resultado['id'] = doc.id
            
            # Converter timestamps para string
            if 'data_processamento' in resultado:
                resultado['data_processamento'] = resultado['data_processamento'].isoformat()
            
            resultados.append(resultado)
        
        return jsonify({
            'total': len(resultados),
            'limit': limit,
            'offset': offset,
            'resultados': resultados
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar resultados: {str(e)}")
        return jsonify({'erro': str(e)}), 500


@app.route('/resultados/search', methods=['GET'])
def buscar_por_nome():
    """
    Buscar análises por nome de arquivo
    Parâmetros:
    - nome: substring do nome do arquivo
    - limit: número máximo de resultados (padrão: 10)
    """
    try:
        nome = request.args.get('nome', '').lower()
        limit = int(request.args.get('limit', 10))
        
        if not nome:
            return jsonify({'erro': 'Parâmetro "nome" é obrigatório'}), 400
        
        logger.info(f"Buscando resultados com nome contendo: {nome}")
        
        # Firestore não suporta busca case-insensitive diretamente
        # Então consultamos todos e filtramos em Python (não recomendado para grandes volumes)
        docs = db.collection('analises_imagens').order_by(
            'data_processamento',
            direction=firestore.Query.DESCENDING
        ).limit(100).stream()
        
        resultados = []
        for doc in docs:
            resultado = doc.to_dict()
            if nome in resultado.get('nome_arquivo', '').lower():
                resultado['id'] = doc.id
                if 'data_processamento' in resultado:
                    resultado['data_processamento'] = resultado['data_processamento'].isoformat()
                resultados.append(resultado)
                
                if len(resultados) >= limit:
                    break
        
        return jsonify({
            'busca': nome,
            'total': len(resultados),
            'resultados': resultados
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar: {str(e)}")
        return jsonify({'erro': str(e)}), 500


@app.route('/resultados/<doc_id>/labels', methods=['GET'])
def obter_labels(doc_id):
    """Obter apenas os labels detectados de uma análise"""
    try:
        doc = db.collection('analises_imagens').document(doc_id).get()
        
        if not doc.exists:
            return jsonify({'erro': 'Documento não encontrado'}), 404
        
        resultado = doc.to_dict()
        labels = resultado.get('resultados', {}).get('labels', [])
        
        # Ordenar por score (confiança)
        labels_ordenados = sorted(labels, key=lambda x: x['score'], reverse=True)
        
        return jsonify({
            'documento': doc_id,
            'total_labels': len(labels_ordenados),
            'labels': labels_ordenados
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter labels: {str(e)}")
        return jsonify({'erro': str(e)}), 500


@app.route('/resultados/<doc_id>/texto', methods=['GET'])
def obter_texto(doc_id):
    """Obter o texto detectado (OCR) de uma análise"""
    try:
        doc = db.collection('analises_imagens').document(doc_id).get()
        
        if not doc.exists:
            return jsonify({'erro': 'Documento não encontrado'}), 404
        
        resultado = doc.to_dict()
        dados = resultado.get('resultados', {})
        
        return jsonify({
            'documento': doc_id,
            'texto_completo': dados.get('texto_completo', ''),
            'total_fragmentos': len(dados.get('textos', [])),
            'fragmentos': dados.get('textos', [])
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter texto: {str(e)}")
        return jsonify({'erro': str(e)}), 500


@app.route('/resultados/<doc_id>/rostos', methods=['GET'])
def obter_rostos(doc_id):
    """Obter informações de rostos detectados"""
    try:
        doc = db.collection('analises_imagens').document(doc_id).get()
        
        if not doc.exists:
            return jsonify({'erro': 'Documento não encontrado'}), 404
        
        resultado = doc.to_dict()
        rostos = resultado.get('resultados', {}).get('rostos', [])
        
        return jsonify({
            'documento': doc_id,
            'total_rostos': len(rostos),
            'rostos': rostos
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter rostos: {str(e)}")
        return jsonify({'erro': str(e)}), 500


@app.route('/resultados/<doc_id>/safe-search', methods=['GET'])
def obter_safe_search(doc_id):
    """Obter análise de segurança de conteúdo"""
    try:
        doc = db.collection('analises_imagens').document(doc_id).get()
        
        if not doc.exists:
            return jsonify({'erro': 'Documento não encontrado'}), 404
        
        resultado = doc.to_dict()
        safe_search = resultado.get('resultados', {}).get('safe_search', {})
        
        return jsonify({
            'documento': doc_id,
            'safe_search': safe_search
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter safe search: {str(e)}")
        return jsonify({'erro': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'api-resultados'}), 200


@app.route('/', methods=['GET'])
def index():
    """Root endpoint com documentação da API"""
    return jsonify({
        'api': 'Consulta de Resultados - Análise de Imagens',
        'endpoints': {
            'GET /resultados': 'Listar todas as análises (com paginação)',
            'GET /resultados/<doc_id>': 'Obter análise completa por ID',
            'GET /resultados/search?nome=xxx': 'Buscar por nome de arquivo',
            'GET /resultados/<doc_id>/labels': 'Obter labels detectados',
            'GET /resultados/<doc_id>/texto': 'Obter texto detectado (OCR)',
            'GET /resultados/<doc_id>/rostos': 'Obter rostos detectados',
            'GET /resultados/<doc_id>/safe-search': 'Obter análise de segurança',
            'GET /health': 'Verificar status da API'
        },
        'parâmetros_opcionais': {
            'limit': 'Número máximo de resultados (padrão: 20)',
            'offset': 'Número de resultados a pular (para paginação)'
        }
    }), 200


if __name__ == '__main__':
    logger.info("Iniciando API de Resultados...")
    logger.info(f"Projeto: {PROJECT_ID}")
    app.run(debug=True, port=5001)
