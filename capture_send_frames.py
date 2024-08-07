import os
import boto3
import subprocess
import logging
import dotenv
import time

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
    # Obter o endpoint de vídeo do Kinesis
    response = kvs_client.get_data_endpoint(
        StreamName=kvs_stream_name,
        APIName='PUT_MEDIA'
    )
    logger.info(f"Using client.")

    endpoint = response['DataEndpoint']
    logger.info(f"endpoint: {endpoint}")

    command = [
        'gst-launch-1.0', 'rtspsrc', f'location={camera_url}', 'short-header=TRUE',
        '!', 'rtph264depay',
        '!', 'decodebin',
        # '!', 'videorate', '!', 'video/x-raw,framerate=1/1',
        '!', 'videoconvert',
        '!', 'x264enc',
        '!', 'video/x-h264,stream-format=avc,alignment=au',
        '!', 'kvssink', 'storage-size=512', f'stream-name={kvs_stream_name}', f'aws-region={aws_region}', f'access-key={aws_access_key}', f'secret-key={aws_secret_key}'
    ]
    while True:
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            logger.info(f"Process command.")

            while True:
                stderr_line = process.stderr.readline()
                if stderr_line:
                    logger.error(f"GStreamer stderr: {stderr_line.strip()}")
                if process.poll() is not None:
                    break

            process.wait()
            logging.info("GStreamer pipeline stopped. Restarting...")

        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            time.sleep(2)

if __name__ == "__main__":
    logger.info("Starting frame capture and send to Kinesis")
    capture_frames()
