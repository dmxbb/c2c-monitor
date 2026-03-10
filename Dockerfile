FROM python:3.10-slim

WORKDIR /app

# 安装 cron
RUN apt-get update && apt-get install -y cron \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY src/ ./src/

# 复制并注册 crontab
COPY crontab /etc/cron.d/monitor
RUN chmod 0644 /etc/cron.d/monitor \
    && crontab /etc/cron.d/monitor

# 启动 cron
CMD ["bash", "-c", "env >> /etc/environment && cron -f"]
