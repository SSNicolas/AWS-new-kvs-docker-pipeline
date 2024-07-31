FROM ubuntu:20.04

# Definir variáveis de ambiente para evitar prompts interativos
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Instalar dependências
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
    pkg-config \
    m4 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Instalar boto3 e outras dependências Python
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Copiar o arquivo .env para o contêiner
COPY .env /app/.env

# Adicionar script para captura e envio de frames
COPY capture_send_frames.py /usr/local/bin/capture_send_frames.py

# Tornar o script executável
RUN chmod +x /usr/local/bin/capture_send_frames.py

# Adicionar um usuário não root
RUN useradd -m appuser
USER appuser

ENTRYPOINT ["python3", "/usr/local/bin/capture_send_frames.py"]
