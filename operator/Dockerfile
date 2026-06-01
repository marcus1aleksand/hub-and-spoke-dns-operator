FROM python:3.13-alpine

RUN apk add --no-cache gcc musl-dev python3-dev

COPY requirements.txt /operator/requirements.txt

WORKDIR /operator

RUN pip install --no-cache-dir -r requirements.txt \
    && apk del gcc musl-dev python3-dev

COPY main.py /operator/main.py
COPY providers/ /operator/providers/

CMD ["python", "/operator/main.py"]
