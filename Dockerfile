FROM python:3.11-slim

WORKDIR /code

# system deps for lxml
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential libxml2-dev libxslt1-dev zlib1g-dev     && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt

COPY . /code
