FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt-get update && apt-get install -y \
    cmake \
    libssl-dev \
    libcurl4-openssl-dev \
    liblog4cplus-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer-plugins-bad1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gstreamer1.0-tools \
    gstreamer1.0-x \
    gstreamer1.0-alsa \
    gstreamer1.0-gl \
    gstreamer1.0-gtk3 \
    gstreamer1.0-qt5 \
    gstreamer1.0-pulseaudio \
    git \
    build-essential \
    tzdata \
    python3 \
    python3-pip \
    ca-certificates \
    pkg-config \
    m4 \
    liblog4cplus-dev \
    libjsoncpp-dev \
    libasio-dev \
    libgl1-mesa-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Clonar e construir o SDK do Kinesis Video Streams Producer
RUN git clone https://github.com/awslabs/amazon-kinesis-video-streams-producer-sdk-cpp.git /opt/amazon-kinesis-video-streams-producer-sdk-cpp \
    && cd /opt/amazon-kinesis-video-streams-producer-sdk-cpp \
    && mkdir -p kinesis-video-native-build \
    && cd kinesis-video-native-build \
    && cmake .. -DBUILD_GSTREAMER_PLUGIN=ON \
    && make \
    && make install

# Ensure GStreamer can find the kvssink plugin
RUN export GST_PLUGIN_PATH=/opt/amazon-kinesis-video-streams-producer-sdk-cpp/build && \
    export LD_LIBRARY_PATH=/opt/amazon-kinesis-video-streams-producer-sdk-cpp/open-source/local/lib

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY .env /app/.env
COPY capture_send_frames.py /usr/local/bin/capture_send_frames.py

RUN chmod +x /usr/local/bin/capture_send_frames.py

ENV GST_PLUGIN_PATH=/opt/amazon-kinesis-video-streams-producer-sdk-cpp/kinesis-video-native-build

RUN useradd -m appuser
USER appuser

ENTRYPOINT ["python3", "/usr/local/bin/capture_send_frames.py"]
