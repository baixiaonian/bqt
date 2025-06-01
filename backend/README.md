# 后端开发说明（FastAPI + SQLite + AI/RAG）

## 目录结构

- main.py         FastAPI 主入口，静态资源托管、API 路由
- models.py       SQLModel 数据模型
- db.py           数据库连接与 Session
- ai_rag.py       AI/RAG 问答逻辑
- requirements.txt Python 依赖

## 启动方式

1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```
2. 启动服务
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## 说明
- 默认使用本地 SQLite 数据库（dag.db）
- 静态资源目录为 ../dist
- AI/RAG 逻辑可在 ai_rag.py 中扩展 