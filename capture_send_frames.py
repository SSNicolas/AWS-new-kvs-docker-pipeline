import os
import boto3
import base64
import subprocess
import threading
import time
import logging
import dotenv

dotenv.load_dotenv('/app/.env')

camera_url = os.getenv('RTSP_URL')
kinesis_stream_name = os.getenv('KINESIS_STREAM_NAME')
aws_region = os.getenv('AWS_REGION')
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info(f"RTSP_URL: {camera_url}")
logger.info(f"KINESIS_STREAM_NAME: {kinesis_stream_name}")
logger.info(f"AWS_REGION: {aws_region}")
logger.info(f"AWS_ACCESS_KEY_ID: {aws_access_key}")
logger.info(f"AWS_SECRET_ACCESS_KEY: {aws_secret_key}")

if not aws_region:
    raise ValueError("AWS_REGION environment variable is not set.")

kinesis_client = boto3.client('kinesis',
                              region_name=aws_region,
                              aws_access_key_id=aws_access_key,
                              aws_secret_access_key=aws_secret_key)


def capture_frames():
    command = [
        'gst-launch-1.0', 'rtspsrc', f'location={camera_url}', 'latency=10',
        '!', 'queue',
        '!', 'rtph264depay',
        '!', 'h264parse',
        '!', 'avdec_h264',
        '!', 'videoconvert',
        '!', 'videorate',
        '!', 'video/x-raw,framerate=1/1',
        '!', 'jpegenc',
    ]
    try:
        while True:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            while True:
                frame = process.stdout.read()
                if frame == b'' and process.poll() is not None:
                    break
                if frame:
                    send_frame_to_kinesis(frame)

            stderr = process.stderr.read().decode('utf-8')
            if stderr:
                logger.error(f"GStreamer stderr: {stderr.strip()}")

            process.wait()
            logging.info("GStreamer pipeline stopped. Restarting...")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")


def send_frame_to_kinesis(frame_data):
    try:
        # frame_base64 = base64.b64encode(frame_data).decode('utf-8')
        response = kinesis_client.put_record(
            StreamName=kinesis_stream_name,
            Data=frame_data,
            PartitionKey='partitionkey'
        )
        logger.info("Sent frame to Kinesis: %s", response)
    except Exception as e:
        logger.error("Failed to send frame to Kinesis: %s", e)


if __name__ == "__main__":
    logger.info("Starting frame capture and send to Kinesis")
    capture_frames()
