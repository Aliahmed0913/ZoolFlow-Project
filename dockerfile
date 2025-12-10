# build stage : 1
FROM python:3.11-slim AS builder 
WORKDIR /app
# DISABLE .PYC                FLUSH STDOUT,STDERR TO SHOW LOGS INSTANTLY
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# apt-get => package manager for os-level (linux based). update=> download metadata list(catalog)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential default-libmysqlclient-dev pkg-config gcc \
    && rm -rf /var/lib/apt/lists/* 

#trigger docker cache mechanism (cache the dependency build layer)
COPY requirements.txt . 
RUN pip install --upgrade pip \
    && pip wheel -r requirements.txt -w /wheels

# runtime stage : 2
FROM python:3.11-slim AS runtime
WORKDIR /app

# to load mysqlclient at the runtime and netcat to check tcp connection
RUN apt-get update && apt-get install -y --no-install-recommends libmariadb3 netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# copy the wheels from the build stage
COPY --from=builder /wheels /wheels
COPY --from=builder /app/requirements.txt .

# --no-index => no internet use
RUN pip install --no-index --find-links=/wheels -r requirements.txt

# /usr/local/bin => default path so we can run this sh without typing the full path in linux shell (this folder owned by the root user)
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
# chmod => gives permissions. x make the script executable , r script can read
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

COPY . .
# chown => change ownership of files/directories  -R recursively apply
RUN useradd -m appuser && chown -R appuser:appuser /app
RUN mkdir -p /app/staticfiles && chown -R appuser:appuser /app/staticfiles
RUN mkdir -p /app/media && chown -R appuser:appuser /app/media
# Containers default to root
USER appuser

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["gunicorn", "stackpay.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

