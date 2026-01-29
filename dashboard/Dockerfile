# ---------- frontend build ----------
FROM node:20-alpine AS frontend

WORKDIR /build
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY script ./script
COPY webpack.config.js tsconfig.json ./
RUN yarn build

# ---------- backend ----------
FROM python:3.14-alpine

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api_server.py mqtt_job.py ./

# frontend artefacts
COPY --from=frontend /build/static ./static

EXPOSE 5000
CMD ["python", "-u", "api_server.py"]
