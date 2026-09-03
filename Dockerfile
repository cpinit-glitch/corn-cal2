FROM python:3.12-slim

WORKDIR /app

# ติดตั้ง dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ดทั้งหมด
COPY . .

# Render จะ inject PORT env var เอง (ค่า default 10000)
ENV PORT=10000
EXPOSE 10000

# ใช้ server.py แทน app.py เพื่อให้รันเป็น ASGI web server บน cloud
CMD ["python", "server.py"]
