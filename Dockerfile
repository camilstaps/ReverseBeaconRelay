from python:3.6-alpine

workdir /usr/src/rbnrelay
copy . .

cmd ["python", "./relay.py"]
