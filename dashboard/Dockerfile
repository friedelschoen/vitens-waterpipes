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

COPY ./ ./

# frontend artefacts
COPY --from=frontend /build/dist/bundle.js* ./static/

EXPOSE 5000
CMD ["python", "-u", "api_server.py"]
