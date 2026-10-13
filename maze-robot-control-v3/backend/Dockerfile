FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends libcairo2 g++ nodejs && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY firmware /firmware
COPY workshop /app/workshop
ENV WORKSHOP_FIRMWARE=/firmware/workshop_robot/workshop_robot.ino
ENV FIRMWARE_DIR=/firmware
ENV WORKSHOP_ASSETS=/app/workshop
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
