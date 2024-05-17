FROM python:3.9-slim
WORKDIR /bot
COPY . /bot
RUN mkdir -p logs

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    systemd \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "bot.py"]
