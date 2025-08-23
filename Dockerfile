FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl git postgresql-client tzdata sudo \
    build-essential libssl-dev zlib1g-dev libcap2-bin \
    libbz2-dev libreadline-dev libsqlite3-dev \
    libncursesw5-dev xz-utils tk-dev libxml2-dev \
    libxmlsec1-dev libffi-dev liblzma-dev \
    libatk-bridge2.0-0 libdbus-glib-1-2 \
    libnss3-dev libgdk-pixbuf2.0-dev libgtk-3-dev libxss-dev \
    libasound2 unzip x11vnc xvfb fluxbox \
    && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app/_hp
RUN chmod +x setup.bash
RUN bash ./setup.bash
ENV PATH="/root/.local/bin:${PATH}"
WORKDIR /app
# Add entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose ports
EXPOSE 80 443 8443 9000

# WORKDIR /app