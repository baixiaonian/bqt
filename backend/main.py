from fastapi import FastAPI, Request, Depends, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlmodel import SQLModel, Session, create_engine, select
import os
from .models import DagGraph
from .db import get_session
from .ai_rag import answer_question

app = FastAPI()

# 先注册所有API
@app.get("/api/dag-list")
def dag_list(session: Session = Depends(get_session)):
    """获取所有DAG图的id和名称列表"""
    result = session.exec(select(DagGraph.id, DagGraph.name)).all()
    return [{"id": r[0], "name": r[1]} for r in result]

@app.get("/api/load-dag")
def load_dag(id: str, session: Session = Depends(get_session)):
    dag = session.get(DagGraph, id)
    return dag

@app.post("/api/save-dag")
def save_dag(
    id: str = Body(...),
    name: str = Body(...),
    data: str = Body(...),
    session: Session = Depends(get_session)
):
    dag = DagGraph(id=id, name=name, data=data)
    session.merge(dag)
    session.commit()
    return {"status": "ok"}

@app.post("/api/ai-qa")
def ai_qa(dag_id: str, question: str, session: Session = Depends(get_session)):
    return answer_question(dag_id, question, session)

@app.delete("/api/delete-dag")
def delete_dag(id: str, session: Session = Depends(get_session)):
    dag = session.get(DagGraph, id)
    if dag:
        session.delete(dag)
        session.commit()
        return {"status": "ok"}
    else:
        return {"status": "not found"}

# 最后挂载静态资源
app.mount("/", StaticFiles(directory="dist", html=True), name="static") 