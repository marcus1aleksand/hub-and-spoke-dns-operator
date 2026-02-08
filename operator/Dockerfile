FROM python:3.14-alpine

COPY requirements.txt /operator/requirements.txt

WORKDIR /operator

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py /operator/main.py

CMD ["python", "/operator/main.py"]
