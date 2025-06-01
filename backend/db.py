from sqlmodel import create_engine, Session, SQLModel

DATABASE_URL = "sqlite:///dag.db"
engine = create_engine(DATABASE_URL, echo=False)

# 初始化表
SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session 