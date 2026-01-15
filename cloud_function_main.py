"""
Cloud Function para Processar Imagens com Vision API
Deploy: gcloud functions deploy processar_imagem --runtime python39 --trigger-resource meu-bucket-imagens --trigger-event google.storage.object.finalize --entry-point processar_imagem
"""
import functions_framework
from google.cloud import storage
from google.cloud import vision
from google.cloud import firestore
from google.cloud import pubsub_v1
import json
from datetime import datetime
import logging

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
        # Ignorar arquivos que não são imagens ou que estão na pasta output
        if not _eh_imagem(file_name) or file_name.startswith("output/"):
            logger.info(f"Arquivo ignorado: {file_name}")
            return {"status": "ignorado"}
        
        logger.info(f"Iniciando processamento: {file_name}")
        
        # PASSO 1: Ler a imagem do Storage
        imagem_bytes = _ler_imagem_storage(bucket_name, file_name)
        
        # PASSO 2: Chamar Vision API
        resultados = _analisar_com_vision_api(imagem_bytes)
        
        # PASSO 3: Guardar resultados no Firestore
        doc_id = _guardar_resultado_firestore(file_name, resultados)
        
        # PASSO 4: Publicar em Pub/Sub (opcional)
        _publicar_notificacao(file_name, doc_id, resultados)
        
        logger.info(f"Processamento concluído para: {file_name}")
        return {"status": "sucesso", "documento": doc_id}
        
    except Exception as e:
        logger.error(f"Erro ao processar imagem: {str(e)}")
        return {"status": "erro", "mensagem": str(e)}


def _eh_imagem(file_name):
    """Verifica se o arquivo é uma imagem"""
    extensoes = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
    return any(file_name.lower().endswith(ext) for ext in extensoes)


def _ler_imagem_storage(bucket_name, file_name):
    """Lê a imagem do Google Cloud Storage"""
    logger.info(f"Lendo imagem do Storage: {bucket_name}/{file_name}")
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    imagem_bytes = blob.download_as_bytes()
    logger.info(f"Imagem lida com sucesso. Tamanho: {len(imagem_bytes)} bytes")
    return imagem_bytes


def _analisar_com_vision_api(imagem_bytes):
    """Chama Google Cloud Vision API para análise"""
    logger.info("Iniciando análise com Vision API...")
    
    image = vision.Image(content=imagem_bytes)
    resultados = {}
    
    try:
        # 1. Label Detection (Detecção de Objetos/Rótulos)
        logger.info("Executando Label Detection...")
        response = vision_client.label_detection(image=image)
        resultados['labels'] = [
            {
                'descricao': label.description,
                'score': float(label.score),
                'mid': label.mid
            }
            for label in response.label_annotations
        ]
        logger.info(f"Labels encontrados: {len(resultados['labels'])}")
        
        # 2. Text Detection (Detecção de Texto - OCR)
        logger.info("Executando Text Detection...")
        response = vision_client.text_detection(image=image)
        if response.text_annotations:
            # Primeiro elemento é o texto completo
            resultados['texto_completo'] = response.text_annotations[0].description if response.text_annotations else ""
            resultados['textos'] = [
                {
                    'texto': text.description,
                    'confianca': float(text.confidence) if text.confidence else 0
                }
                for text in response.text_annotations[1:] if text.description.strip()  # Skip primeiro (texto completo)
            ]
        else:
            resultados['texto_completo'] = ""
            resultados['textos'] = []
        logger.info(f"Textos encontrados: {len(resultados['textos'])}")
        
        # 3. Face Detection (Detecção de Rostos)
        logger.info("Executando Face Detection...")
        response = vision_client.face_detection(image=image)
        resultados['rostos'] = [
            {
                'confianca': float(face.detection_confidence),
                'alegria': int(face.joy_likelihood),
                'surpresa': int(face.surprise_likelihood),
                'raiva': int(face.anger_likelihood),
                'tristeza': int(face.sorrow_likelihood)
            }
            for face in response.face_annotations
        ]
        logger.info(f"Rostos detectados: {len(resultados['rostos'])}")
        
        # 4. Safe Search Detection (Classificação de conteúdo seguro)
        logger.info("Executando Safe Search Detection...")
        response = vision_client.safe_search_detection(image=image)
        resultados['safe_search'] = {
            'adulto': str(response.safe_search_annotation.adult),
            'violencia': str(response.safe_search_annotation.violence),
            'spoof': str(response.safe_search_annotation.spoof),
            'medical': str(response.safe_search_annotation.medical),
            'racy': str(response.safe_search_annotation.racy)
        }
        
        # 5. Image Properties (Propriedades da imagem - cores dominantes)
        logger.info("Executando Image Properties...")
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
        
        logger.info("Análise com Vision API concluída com sucesso")
        return resultados
        
    except Exception as e:
        logger.error(f"Erro na análise Vision API: {str(e)}")
        raise


def _guardar_resultado_firestore(nome_arquivo, resultados):
    """Guarda os resultados de análise no Firestore"""
    logger.info("Guardando resultados no Firestore...")
    
    dados = {
        'nome_arquivo': nome_arquivo,
        'data_processamento': datetime.now(),
        'resultados': resultados,
        'status': 'processado',
        'total_labels': len(resultados.get('labels', [])),
        'total_textos': len(resultados.get('textos', [])),
        'total_rostos': len(resultados.get('rostos', []))
    }
    
    try:
        # Adicionar documento à coleção 'analises_imagens'
        _, doc_ref = db.collection('analises_imagens').add(dados)
        logger.info(f"Documento criado no Firestore: {doc_ref.id}")
        return doc_ref.id
        
    except Exception as e:
        logger.error(f"Erro ao guardar no Firestore: {str(e)}")
        raise


def _publicar_notificacao(nome_arquivo, doc_id, resultados):
    """Publica mensagem em Pub/Sub para notificar outros serviços"""
    try:
        logger.info("Publicando notificação em Pub/Sub...")
        topic_path = publisher_client.topic_path(PROJECT_ID, TOPIC_ID)
        
        mensagem = {
            'nome_arquivo': nome_arquivo,
            'documento_firestore': doc_id,
            'tempo_processamento': datetime.now().isoformat(),
            'total_labels': len(resultados.get('labels', [])),
            'total_textos': len(resultados.get('textos', [])),
            'total_rostos': len(resultados.get('rostos', [])),
            'status': 'processado_sucesso'
        }
        
        # Publicar mensagem
        future = publisher_client.publish(
            topic_path, 
            json.dumps(mensagem).encode('utf-8')
        )
        
        message_id = future.result()
        logger.info(f"Notificação publicada com ID: {message_id}")
        
    except Exception as e:
        logger.warning(f"Não foi possível publicar notificação: {str(e)}")
        # Não falhar o processamento se Pub/Sub falhar
