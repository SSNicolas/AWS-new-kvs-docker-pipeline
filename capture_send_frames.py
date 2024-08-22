import os
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

if not aws_region:
    raise ValueError("AWS_REGION environment variable is not set.")

logger.info(f"Client created.")

# Substituir a pipeline anterior pelo comando fornecido
command = [
    'gst-launch-1.0',
    'rtspsrc', f'location={camera_url}', 'short-header=TRUE',
    '!', 'rtph264depay',
    '!', 'video/x-h264,format=avc,alignment=au',
    '!', 'kvssink', f'stream-name={kvs_stream_name}', 'storage-size=512',
    f'access-key={aws_access_key}', f'secret-key={aws_secret_key}', f'aws-region={aws_region}'
]

try:
    logger.info("Starting GStreamer pipeline.")
    # Iniciar o pipeline GStreamer
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Monitorar o processo continuamente
    while True:
        output = process.stdout.readline()
        error = process.stderr.readline()

        if output:
            logger.info(f"STDOUT: {output.strip()}")

        if error:
            logger.error(f"STDERR: {error.strip()}")

        # Se o processo terminar, sair do loop
        if process.poll() is not None:
            break

    process.wait()

except Exception as e:
    logger.error(f"Erro ao executar o pipeline GStreamer: {e}")
finally:
    if process:
        process.terminate()
        logger.info("GStreamer pipeline terminated.")
