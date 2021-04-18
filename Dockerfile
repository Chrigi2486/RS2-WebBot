FROM python:3.7.10
MAINTAINER Chrigi2486 <chrigi2486@gmail.com>

EXPOSE 6969

RUN mkdir -p /app
COPY . /app
WORKDIR /app

RUN pip install -r ./requirements.txt
CMD python -u main.py
