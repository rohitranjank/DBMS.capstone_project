FROM node:20 AS fe
WORKDIR /fe
COPY frontend/package*.json ./
RUN npm install
COPY frontend .
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend .
COPY --from=fe /fe/dist ./static_dist
CMD ["sh", "-c", "python seed.py && gunicorn -w 2 -b 0.0.0.0:${PORT:-5000} run:app"]
