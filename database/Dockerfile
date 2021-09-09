FROM python:3.8-slim-buster

EXPOSE 9099

WORKDIR /pynini

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD ["python3", "-u", "DBConnector.py"]
