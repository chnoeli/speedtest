FROM python:3.11-slim-bookworm

# Install basics
RUN apt-get update && apt-get install -y iperf3 curl cron

# Install speedtest cli
RUN curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | bash
RUN apt-get install speedtest

WORKDIR /app
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY speedtest.py .
COPY entrypoint.sh .

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT [ "/bin/bash", "/app/entrypoint.sh"]
# ENTRYPOINT ["python", "/app/speedtest.py"]