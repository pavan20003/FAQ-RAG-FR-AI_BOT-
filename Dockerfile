FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/model-cache

WORKDIR /app
RUN addgroup --system app && adduser --system --ingroup app app
RUN mkdir -p /model-cache && chown -R app:app /model-cache
COPY requirements.txt .
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu "torch==2.7.1+cpu"
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY widget ./widget
COPY data/demo_site ./data/demo_site
ENV TOKENIZERS_PARALLELISM=false
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=20m --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
