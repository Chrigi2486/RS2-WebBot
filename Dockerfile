FROM python:3.6.8
MAINTAINER Romaric Philogène <rphilogene@qovery.com>

EXPOSE 6969

RUN mkdir -p /app
COPY . /app
WORKDIR /app

RUN pip install -r ./requirements.txt
CMD python -u main.py
