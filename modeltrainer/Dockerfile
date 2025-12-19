FROM python:3.11-slim

WORKDIR /app

COPY ./ /app

RUN pip install --no-cache-dir -r /app/requirements.txt

CMD ["python", "/app/create_model.py", "--csv", "/data/data.csv", "--output", "/model/"]
