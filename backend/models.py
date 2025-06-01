from sqlmodel import SQLModel, Field
from typing import Optional
from sqlalchemy import Text

class DagGraph(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str  # 图名称
    data: str = Field(sa_column=Text)  # 存储整个 DAG 的 JSON 字符串 