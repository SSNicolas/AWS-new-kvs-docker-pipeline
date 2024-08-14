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

kvs_client = boto3.client('kinesisvideo',
                              region_name=aws_region,
                              aws_access_key_id=aws_access_key,
                              aws_secret_access_key=aws_secret_key)

logger.info(f"Client created.")


def capture_frames():
    while True:
        # Obter o endpoint de vídeo do Kinesis
        response = kvs_client.get_data_endpoint(
            StreamName=kvs_stream_name,
            APIName='PUT_MEDIA'
        )
        logger.info(f"Using client.")

        endpoint = response['DataEndpoint']
        logger.info(f"endpoint: {endpoint}")

        command = [
            'gst-launch-1.0',
            'rtspsrc', f'location={camera_url}', 'latency=0',
            '!', 'rtph264depay',
            '!', 'h264parse',
            '!', 'queue', 'leaky=downstream',  # Descarta frames mais antigos se necessário
            '!', 'kvssink', f'stream-name={kvs_stream_name}', 'storage-size=512', f'aws-region={aws_region}', f'access-key={aws_access_key}', f'secret-key={aws_secret_key}'
        ]
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"Process command.")

            while True:
                output = process.stdout.readline()
                error = process.stderr.readline()

                if output:
                    logger.info(f"STDOUT: {output.strip()}")

                if error:
                    logger.error(f"STDERR: {error.strip()}")

                # Se o processo terminar, sai do loop
                if output == '' and process.poll() is not None:
                    break

            process.wait()

            time.sleep(2)
        except subprocess.CalledProcessError as e:
            print(f"Erro ao executar o pipeline GStreamer: {e}")
            print(e.stderr.decode())  # Imprime o erro retornado pelo GStreamer
            time.sleep(2)



if __name__ == "__main__":
    logger.info("Starting frame capture and send to Kinesis")
    capture_frames()
