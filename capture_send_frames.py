import sys
import gi
import boto3
import os
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

gi.require_version('Gst', '1.0')
gi.require_version('GstRtsp', '1.0')
from gi.repository import Gst

# Inicialize o GStreamer
Gst.init(None)

# Obtenha as variáveis de ambiente
RTSP_URL = os.getenv("RTSP_URL")
KVS_STREAM_NAME = os.getenv("KVS_STREAM_NAME")
AWS_REGION = os.getenv("AWS_REGION")

if not RTSP_URL or not KVS_STREAM_NAME or not AWS_REGION:
    print("Erro: As variáveis de ambiente RTSP_URL, KVS_STREAM_NAME e AWS_REGION devem estar configuradas.")
    sys.exit(1)

# Função de callback para lidar com mensagens de erro do GStreamer
def on_error(bus, message):
    err, debug = message.parse_error()
    print(f"Error: {err}, {debug}")
    Gst.main_quit()

# Configura a pipeline do GStreamer
def create_pipeline():
    pipeline_str = f"""
        rtspsrc location={RTSP_URL} ! 
        rtph264depay ! 
        h264parse ! 
        kvssink stream-name={KVS_STREAM_NAME} 
        storage-size=512 
        aws-region={AWS_REGION}
    """
    return Gst.parse_launch(pipeline_str)

def main():
    pipeline = create_pipeline()
    if not pipeline:
        print("Failed to create pipeline")
        sys.exit(1)

    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message::error", on_error)

    # Inicie a pipeline
    pipeline.set_state(Gst.State.PLAYING)

    # Main loop
    try:
        Gst.main()
    except KeyboardInterrupt:
        print("Shutting down pipeline...")
    finally:
        pipeline.set_state(Gst.State.NULL)

if __name__ == "__main__":
    # Verifique as credenciais da AWS
    try:
        boto3.client('sts').get_caller_identity()
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"AWS credentials error: {e}")
        sys.exit(1)

    main()
