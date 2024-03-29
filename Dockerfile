FROM python:3.8.6-buster

RUN apt update
RUN apt-get update && apt-get install -y cron
RUN alias py=python

ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/influxnews

COPY ./influxnews .
COPY ./requirements.txt /usr/src/influxnews/

COPY ./firebase-creds.json /usr/src/influxnews/accounts/

RUN pip install --no-cache-dir -r requirements.txt

# django-crontab logfile
RUN mkdir /cron
RUN touch /cron/influxnews.log

EXPOSE 8000

CMD service cron start && python manage.py crontab add && gunicorn influxnews.wsgi:application --bind 0.0.0.0:$PORT