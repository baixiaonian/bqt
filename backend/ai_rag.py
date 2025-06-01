def answer_question(dag_id, question, session):
    # TODO: 实现 RAG 检索增强问答
    # 1. 从数据库加载 dag_id 对应的图信息
    # 2. 组织知识片段
    # 3. 检索相关内容
    # 4. 调用大模型生成答案
    return {"answer": f"[模拟回复] DAG({dag_id}) 问题：{question}"} 