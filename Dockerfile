FROM ubuntu:latest as ffmpeg-builder

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y wget tar xz-utils && \
    wget https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz -O ffmpeg-git-amd64-static.tar.xz && \
    mkdir -p /ffmpeg-static && \
    tar -xf ffmpeg-git-amd64-static.tar.xz -C /ffmpeg-static --strip-components=1
RUN apt-get clean autoclean && \
    apt-get autoremove --yes && \
    rm -rf /var/lib/{apt,dpkg,cache,log}/


    
    # install specific version of ffmpeg
    
FROM python:3.10.11-slim-buster
COPY --from=ffmpeg-builder /ffmpeg-static/ffmpeg /usr/local/bin/ffmpeg
COPY --from=ffmpeg-builder /ffmpeg-static/ffprobe /usr/local/bin/ffprobe

# Set the working directory
WORKDIR /app
# Copy the requirements file into the container
COPY requirements.txt .
# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt
# Copy the rest of the application code into the container
COPY . .
# Complile translations
RUN pybabel compile -d lang

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
