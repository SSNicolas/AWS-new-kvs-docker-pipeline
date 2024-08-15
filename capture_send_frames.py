import os
import time

import boto3
import subprocess
import logging
import dotenv

dotenv.load_dotenv('/app/.env')

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
logger.info(f"AWS_SECRET_ACCESS_KEY: {aws_secret_key}")

if not aws_region:
    raise ValueError("AWS_REGION environment variable is not set.")


logger.info(f"Client created.")


def capture_frames():
    while True:
        command = [
            'gst-launch-1.0',
            'rtspsrc', f'location={camera_url}', 'latency=0',
            '!', 'rtph264depay',
            '!', 'h264parse',
            '!', 'queue', 'leaky=downstream', 'max-size-buffers=1', # Descarta frames mais antigos se necessário
            '!', 'kvssink', f'stream-name={kvs_stream_name}', 'storage-size=512', f'aws-region={aws_region}', f'access-key={aws_access_key}', f'secret-key={aws_secret_key}'
        ]
        try:
            subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logger.info(f"Process command.")

            time.sleep(5)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao executar o pipeline GStreamer: {e}")
            print(e.stderr.decode())  # Imprime o erro retornado pelo GStreamer
            time.sleep(5)



if __name__ == "__main__":
    logger.info("Starting frame capture and send to Kinesis")
    capture_frames()
