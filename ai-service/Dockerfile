FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        --index-url https://download.pytorch.org/whl/cpu \
        torch==2.13.0+cpu \
        torchvision==0.28.0+cpu \
    && pip install --no-cache-dir \
        -r requirements.txt

COPY app ./app

RUN mkdir -p ./models

COPY models/wound-efficientnet-b0-binary.pt \
    ./models/wound-efficientnet-b0-binary.pt

COPY models/wound-type-efficientnet-b0-v1.pt \
    ./models/wound-type-efficientnet-b0-v1.pt

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s \
    --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]