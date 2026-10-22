import os

# Gunicorn configuration file for PackGuard AI on Render & production environments

# Bind to 0.0.0.0 and port supplied by Render ($PORT)
port = os.getenv("PORT", "5000")
bind = f"0.0.0.0:{port}"

# Concurrency & threading
# Multimodal artwork analysis and PDF rendering benefit from thread concurrency
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
threads = int(os.getenv("GUNICORN_THREADS", "4"))
worker_class = "gthread"

# Extended timeout (120s) for two-stage vision and regulatory AI processing
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = 30
keepalive = 5

# Logging to standard output for Render Log Streams
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")

# Worker recycling to prevent memory bloat over long lifespans
max_requests = 1000
max_requests_jitter = 100
