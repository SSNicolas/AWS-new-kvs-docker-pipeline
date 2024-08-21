import os
import time
import logging
import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject


camera_url = os.getenv('RTSP_URL')
kvs_stream_name = os.getenv('KVS_STREAM_NAME')
aws_region = os.getenv('AWS_REGION')
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"RTSP_URL: {camera_url}")
logger.info(f"KVS_STREAM_NAME: {kvs_stream_name}")
logger.info(f"AWS_REGION: {aws_region}")
logger.info(f"AWS_ACCESS_KEY_ID: {aws_access_key}")

if not aws_region:
    raise ValueError("AWS_REGION environment variable is not set.")

logger.info(f"Client created.")

# Inicializando o GStreamer
Gst.init(None)

def on_error(bus, msg):
    logger.error(f"Error: {msg.parse_error()}")


def on_eos(bus, msg):
    logger.info("End-Of-Stream reached.")
    Gst.main_quit()


def capture_frames():
    pipeline_str = (
        f"rtspsrc location={camera_url} latency=0 ! "
        "rtph264depay ! h264parse ! queue leaky=downstream ! "
        f"kvssink stream-name={kvs_stream_name} storage-size=512 "
        f"aws-region={aws_region} access-key={aws_access_key} secret-key={aws_secret_key}"
    )

    pipeline = Gst.parse_launch(pipeline_str)

    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message::error", on_error)
    bus.connect("message::eos", on_eos)

    logger.info("Starting the GStreamer pipeline.")
    pipeline.set_state(Gst.State.PLAYING)

    try:
        loop = GObject.MainLoop()
        loop.run()
    except Exception as e:
        logger.error(f"Exception in GStreamer loop: {e}")
    finally:
        pipeline.set_state(Gst.State.NULL)
        logger.info("GStreamer pipeline terminated.")


if __name__ == "__main__":
    logger.info("Starting frame capture and send to Kinesis")
    capture_frames()
