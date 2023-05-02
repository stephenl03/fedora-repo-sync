FROM python:3.11-slim-buster

WORKDIR /app

RUN apt-get update && \
    apt-get install -y rsync ssh

COPY sync_fedora_repo.py ./

CMD [ "python", "./sync_fedora_repo.py" ]