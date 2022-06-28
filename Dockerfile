FROM python:3.10.5-slim-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

CMD ["gunicorn", "app:app", "-b", "0.0.0.0:10092"]
