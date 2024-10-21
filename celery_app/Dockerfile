FROM python:3.12-slim

WORKDIR /app

RUN pip install --upgrade pip

COPY celery_app/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY celery_app /app/celery_app
COPY .env /app/.env

CMD ["celery", "-A", "celery_app.tasks", "worker", "--loglevel=info"]
