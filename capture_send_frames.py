import os
import logging
import gi
import dotenv

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
camera_url = os.getenv('RTSP_URL')
kvs_stream_name = os.getenv('KVS_STREAM_NAME')
aws_region = os.getenv('AWS_REGION')
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')

if not all([camera_url, kvs_stream_name, aws_region, aws_access_key, aws_secret_key]):
    logger.error("Algumas variáveis de ambiente necessárias não estão definidas.")
    raise ValueError("Verifique as variáveis de ambiente obrigatórias.")

logger.info(
    f"Configurando captura do stream RTSP de {camera_url} para o KVS stream {kvs_stream_name} na região {aws_region}."
)

# Inicialização do GStreamer
Gst.init(None)


def on_message(bus, message, loop):
    msg_type = message.type
    if msg_type == Gst.MessageType.EOS:
        logger.info("Fim do stream.")
        loop.quit()
    elif msg_type == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        logger.error(f"Erro: {err}, {debug}")
        loop.quit()


def start_pipeline():
    # Definição do pipeline GStreamer
    pipeline_str = (
        f"rtspsrc location={camera_url} latency=0 ! "
        "rtph264depay ! h264parse ! "
        "x264enc tune=zerolatency bitrate=5000 speed-preset=superfast ! "  # Adicionando codificação H.264 consistente
        "video/x-h264,profile=baseline ! "  # Forçando o perfil baseline para consistência
        "queue leaky=downstream ! "
        f"kvssink stream-name={kvs_stream_name} aws-region={aws_region} access-key={aws_access_key} secret-key={aws_secret_key}"
    )

    logger.info(f"Pipeline GStreamer: {pipeline_str}")

    # Criação do pipeline
    pipeline = Gst.parse_launch(pipeline_str)

    if not pipeline:
        logger.error("Falha ao criar o pipeline GStreamer. Verifique a configuração.")
        return

    bus = pipeline.get_bus()

    if not bus:
        logger.error("Falha ao obter o bus do pipeline GStreamer.")
        return

    bus.add_signal_watch()

    # Conectar o gerenciamento de mensagens
    loop = GObject.MainLoop()
    bus.connect("message", on_message, loop)

    # Iniciar o pipeline
    logger.info("Iniciando o pipeline GStreamer.")
    pipeline.set_state(Gst.State.PLAYING)

    try:
        loop.run()
    except Exception as e:
        logger.error(f"Exceção no loop GStreamer: {e}")
    finally:
        pipeline.set_state(Gst.State.NULL)
        logger.info("Pipeline GStreamer finalizado.")


if __name__ == "__main__":
    logger.info("Captura de frames iniciada e envio para Kinesis.")
    start_pipeline()
