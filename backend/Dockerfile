# syntax=docker/dockerfile:1
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN --mount=type=secret,id=host_ca \
    if [ -s /run/secrets/host_ca ]; then \
        cat /etc/ssl/certs/ca-certificates.crt /run/secrets/host_ca > /tmp/build-ca.pem; \
        export PIP_CERT=/tmp/build-ca.pem; \
    fi \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -f /tmp/build-ca.pem \
    && useradd -m -u 10001 appuser
COPY backend/common/ /app/common/
ARG SERVICE_FOLDER
COPY backend/${SERVICE_FOLDER}/ /app/application/
RUN mkdir -p /data && chown -R appuser:appuser /data
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=4s --start-period=15s --retries=3 CMD python -c 'import urllib.request;urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=3)' || exit 1
CMD ["uvicorn", "application.main:app", "--host", "0.0.0.0", "--port", "8000"]
