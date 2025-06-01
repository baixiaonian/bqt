# 构建前端
FROM node:18 AS frontend-build
WORKDIR /app/frontend
COPY frontend/ ./
RUN npm install && npm run build

# 构建后端
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/dist ./dist
COPY dag.db ./dag.db

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"] 