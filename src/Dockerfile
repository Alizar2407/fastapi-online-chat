FROM python:3.12-slim

WORKDIR /app

RUN pip install --upgrade pip

COPY src/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY src /app/src
COPY celery_app /app/celery_app
COPY src/.env /app/src/.env

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
