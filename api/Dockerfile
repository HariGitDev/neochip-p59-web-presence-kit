FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --no-create-home contact \
    && mkdir /data && chown contact:contact /data
COPY app.py .

USER contact
VOLUME ["/data"]
EXPOSE 8060
HEALTHCHECK --interval=30s --timeout=5s CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8060/healthz', timeout=3).close()"]
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8060", "--no-access-log", "--no-proxy-headers"]
