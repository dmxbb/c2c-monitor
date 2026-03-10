FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY crontab /etc/cron.d/monitor

RUN apt-get update && apt-get install -y cron \
    && chmod 0644 /etc/cron.d/monitor \
    && crontab /etc/cron.d/monitor

CMD ["cron", "-f"]

*/1 * * * * python /app/src/get_gate_c2c_data.py >> /var/log/monitor.log 2>&1
