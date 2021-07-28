# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /pynini

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "-u", "co2Virtual.py"]



