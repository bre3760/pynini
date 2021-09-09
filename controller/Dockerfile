# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /controller

ADD config.json /

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "-u", "controlsys.py"]