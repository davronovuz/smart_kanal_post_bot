FROM python:3.11-slim

# Working directory
WORKDIR /app

# Kerakli paketlarni o'rnatish
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Requirements ni oldin copy qilish (cache uchun)
COPY requirements.txt .

# Kutubxonalarni o'rnatish
RUN pip install --no-cache-dir -r requirements.txt

# Loyihani copy qilish
COPY . .

# Botni ishga tushirish
CMD ["python", "main.py"]