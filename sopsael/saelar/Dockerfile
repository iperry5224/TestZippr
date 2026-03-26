# SAELAR - NIST 800-53 Security Assessment (SOPSAEL)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8443 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir openpyxl>=3.1.0 XlsxWriter>=3.1.0

COPY . .
RUN mkdir -p /app/ssl_certs /app/assets /root/.aws

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8443

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8443/_stcore/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["streamlit", "run", "nist_setup.py", "--server.port=8443", "--server.address=0.0.0.0"]
