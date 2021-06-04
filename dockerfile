FROM python:3.9.5-slim-buster as build
EXPOSE 5000
RUN apt update && apt upgrade -y && apt install -y ffmpeg
WORKDIR /app
COPY . .
RUN pip3 install --no-cache-dir -r requirements.txt
ENTRYPOINT ["/bin/bash", "./setup.sh" ]