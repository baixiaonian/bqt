# DAG 编辑器后端接口文档

## 1. 获取图列表
- **接口**：`GET /api/dag-list`
- **描述**：获取所有DAG图的id和名称列表。
- **请求参数**：无
- **返回示例**：
```
[
  {"id": "uuid1", "name": "图A"},
  {"id": "uuid2", "name": "图B"}
]
```

---

## 2. 加载指定DAG图
- **接口**：`GET /api/load-dag`
- **描述**：根据id加载指定DAG图的全部数据。
- **请求参数**：
  - `id`（string，必填）：DAG图的唯一标识
- **返回示例**：
```
{
  "id": "uuid1",
  "name": "图A",
  "data": "{...}" // DAG图的JSON字符串
}
```

---

## 3. 保存DAG图
- **接口**：`POST /api/save-dag`
- **描述**：保存（新增或更新）DAG图数据。
- **请求参数（JSON Body）**：
```
{
  "id": "uuid1",      // DAG图唯一标识
  "name": "图A",      // DAG图名称
  "data": "{...}"     // DAG图的JSON字符串
}
```
- **返回示例**：
```
{"status": "ok"}
```

---

## 4. AI问答接口（保留原有）
- **接口**：`POST /api/ai-qa`
- **描述**：对指定DAG图进行AI问答。
- **请求参数（JSON Body）**：
```
{
  "dag_id": "uuid1",
  "question": "xxx"
}
```
- **返回**：AI回答内容

---

## 5. 删除DAG图
- **接口**：`DELETE /api/delete-dag`
- **描述**：根据id删除指定DAG图。
- **请求参数**：
  - `id`（string，必填）：DAG图的唯一标识（query参数）
- **返回示例**：
```
{"status": "ok"}
```

---

## 说明
- 所有接口均为RESTful风格。
- 图数据采用JSON字符串存储，前端需自行序列化/反序列化。
- 图的唯一标识`id`由前端生成（如UUID）。 