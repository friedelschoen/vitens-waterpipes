FROM python:3.14-alpine

WORKDIR /app

COPY ./ /app

RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 5000

CMD ["python", "-u", "api_server.py"]
