FROM python:3.11-slim

WORKDIR /app

# System dependencies install karein
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Requirements install karein
COPY requirements.txt .
#RUN pip install --default-timeout=1000 --no-cache-dir --no-deps-check -r requirements.txt
RUN pip install --no-cache-dir --default-timeout=1000 --index-url https://pypi.org/simple -r requirements.txt

# Application code copy karein
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]