FROM python:3.12-slim
WORKDIR /bridge
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY serial_bridge.py .
ENTRYPOINT ["python", "serial_bridge.py"]
