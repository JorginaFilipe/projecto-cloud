"""
Subscriber de Pub/Sub para Notificações
Escuta por mensagens quando imagens são processadas
"""
from google.cloud import pubsub_v1
from google.cloud import firestore
import json
import logging
from datetime import datetime

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "projectcloud-484416"
SUBSCRIPTION_ID = "imagem-processada-sub"

# Inicializar cliente
db = firestore.Client()


def subscriber_callback(message):
    """Callback executado quando uma mensagem é recebida"""
    try:
        dados = json.loads(message.data.decode('utf-8'))
        
        logger.info("=" * 60)
        logger.info("📬 NOTIFICAÇÃO RECEBIDA")
        logger.info("=" * 60)
        logger.info(f"  📄 Arquivo: {dados['nome_arquivo']}")
        logger.info(f"  🆔 Documento Firestore: {dados['documento_firestore']}")
        logger.info(f"  🏷️  Labels encontrados: {dados['total_labels']}")
        logger.info(f"  📝 Textos encontrados: {dados['total_textos']}")
        logger.info(f"  👤 Rostos detectados: {dados['total_rostos']}")
        logger.info(f"  ⏰ Tempo: {dados['tempo_processamento']}")
        logger.info("=" * 60)
        
        # Aqui você pode adicionar lógica adicional:
        # - Enviar email ao utilizador
        # - Enviar notificação push
        # - Fazer webhook para outro serviço
        # - Atualizar base de dados de utilizadores
        
        # Exemplo: Guardar notificação no Firestore
        guardar_notificacao(dados)
        
        # Reconhecer a mensagem (remove da fila)
        message.ack()
        logger.info("✅ Mensagem processada com sucesso")
        
    except Exception as e:
        logger.error(f"❌ Erro ao processar notificação: {e}")
        # Não fazer ack para reprocessar a mensagem mais tarde
        message.nack()


def guardar_notificacao(dados):
    """Guarda a notificação num histórico no Firestore"""
    try:
        notificacao = {
            'arquivo': dados['nome_arquivo'],
            'documento_firestore': dados['documento_firestore'],
            'total_labels': dados['total_labels'],
            'total_textos': dados['total_textos'],
            'total_rostos': dados['total_rostos'],
            'timestamp': datetime.now(),
            'status': dados.get('status', 'processado_sucesso')
        }
        
        db.collection('notificacoes').add(notificacao)
        logger.info("💾 Notificação guardada no Firestore")
        
    except Exception as e:
        logger.error(f"Erro ao guardar notificação: {e}")


def enviar_email(email_usuario, dados):
    """
    Exemplo de função para enviar email ao utilizador
    Você pode usar SendGrid, Mailgun, Google Cloud Functions, etc.
    """
    logger.info(f"📧 Email será enviado para: {email_usuario}")
    # Implementar envio de email aqui
    pass


def enviar_webhook(url_webhook, dados):
    """
    Exemplo de função para enviar webhook
    """
    import requests
    
    try:
        response = requests.post(url_webhook, json=dados, timeout=10)
        logger.info(f"🌐 Webhook enviado com status: {response.status_code}")
    except Exception as e:
        logger.error(f"Erro ao enviar webhook: {e}")


def iniciar_subscriber():
    """Iniciar subscription para ouvir notificações"""
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    
    logger.info(f"🔊 Iniciando subscriber...")
    logger.info(f"📌 Projeto: {PROJECT_ID}")
    logger.info(f"📌 Subscription: {SUBSCRIPTION_ID}")
    logger.info(f"Pressione Ctrl+C para sair\n")
    
    # Criar subscription se não existir (opcional)
    try:
        subscriber.get_subscription(request={"subscription": subscription_path})
    except:
        logger.info("Criando nova subscription...")
        topic_path = subscriber.topic_path(PROJECT_ID, "imagem-processada")
        subscriber.create_subscription(
            request={"name": subscription_path, "topic": topic_path}
        )
    
    # Configurar streaming pull
    streaming_pull_future = subscriber.subscribe(
        subscription_path,
        callback=subscriber_callback,
        flow_control=pubsub_v1.types.FlowControl(max_messages=10, max_bytes=1000*1024*1024),
    )
    
    print("\n" + "=" * 60)
    print("✅ Subscriber ativo! Aguardando notificações...")
    print("=" * 60 + "\n")
    
    try:
        streaming_pull_future.result()
    except KeyboardInterrupt:
        logger.info("\n⏹️  Parando subscriber...")
        streaming_pull_future.cancel()
        logger.info("✅ Subscriber finalizado")


if __name__ == '__main__':
    iniciar_subscriber()
