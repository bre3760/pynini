# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /pynini
ADD influxDB.py /
ADD query.py /
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "-u", "temphum.py"]



