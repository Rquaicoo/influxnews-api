FROM python:3.8.6-buster

RUN apt update
RUN apt-get install cron -y
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

CMD service cron start && gunicorn influxnews.wsgi:application --bind 0.0.0.0:$PORT