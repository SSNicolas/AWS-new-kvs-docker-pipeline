import os
import logging
import gi
import time

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

# Carregar variáveis de ambiente
camera_url = os.getenv('RTSP_URL')
kvs_stream_name = os.getenv('KVS_STREAM_NAME')
aws_region = os.getenv('AWS_REGION')
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"RTSP_URL: {camera_url}")
logger.info(f"KVS_STREAM_NAME: {kvs_stream_name}")
logger.info(f"AWS_REGION: {aws_region}")
logger.info(f"AWS_ACCESS_KEY_ID: {aws_access_key}")

# Verificar se todas as variáveis de ambiente estão configuradas
if not all([camera_url, kvs_stream_name, aws_region, aws_access_key, aws_secret_key]):
    raise ValueError("One or more environment variables are not set.")

logger.info("Client created.")

# Inicializando o GStreamer
Gst.init(None)


def on_error(bus, msg, loop):
    err, debug = msg.parse_error()
    logger.error(f"Error received from element {msg.src.get_name()}: {err.message}")
    logger.error(f"Debugging information: {debug if debug else 'None'}")
    loop.quit()


def on_eos(bus, msg, loop):
    logger.info("End-Of-Stream reached.")
    loop.quit()


def create_pipeline():

    pipeline_str = (
        f"rtspsrc location={camera_url} latency=200 ! "
        "rtph264depay ! h264parse ! "
        f"kvssink stream-name={kvs_stream_name} storage-size=512 "
        f"aws-region={aws_region} access-key={aws_access_key} secret-key={aws_secret_key}"
    )

    return Gst.parse_launch(pipeline_str)

def run_pipeline():
    while True:
        pipeline = create_pipeline()
        if not pipeline:
            logger.error("Failed to create pipeline")
            return

        loop = GObject.MainLoop()

        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", on_error, loop)
        bus.connect("message::eos", on_eos, loop)

        logger.info("Starting the GStreamer pipeline.")
        ret = pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            logger.error("Unable to set the pipeline to the playing state.")
            pipeline.set_state(Gst.State.NULL)
            return

        try:
            loop.run()
        except Exception as e:
            logger.error(f"Exception in GStreamer loop: {e}")
        finally:
            pipeline.set_state(Gst.State.NULL)
            logger.info("GStreamer pipeline terminated.")

        # Tentativa de reconexão após uma breve pausa
        logger.info("Tentando reconectar em 5 segundos...")
        time.sleep(5)

if __name__ == "__main__":
    logger.info("Starting frame capture and send to Kinesis")
    run_pipeline()
