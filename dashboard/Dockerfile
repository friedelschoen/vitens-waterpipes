FROM python:3.14-alpine

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./ /app
EXPOSE 5000
CMD ["python", "-u", "api_server.py"]
