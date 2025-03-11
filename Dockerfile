FROM python:3

ENV PYTHONUNBUFFERED=1 

WORKDIR /app

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

CMD exec gunicorn main:app --timeout 0