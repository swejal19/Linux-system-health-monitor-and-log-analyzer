FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config.json .
COPY logs/sample_system.log ./logs/sample_system.log

RUN mkdir -p /app/reports

CMD ["python", "src/monitor.py"]
