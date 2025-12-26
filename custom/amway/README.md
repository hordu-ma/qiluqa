# pgvector客户端相关命令
```
# 0.创建实例
docker run -itd --name=postgres_client -p 5432:5432 -e POSTGRES_PASSWORD=12456 postgres:latest

# 1.进入实例
docker exec -it postgres_client /bin/bash

# 3.连接pgvector
psql -h 10.143.17.179 -p 5432 -U postgres -d bespin_chat

# 查询语句
select uuid,cmetadata from langchain_pg_embedding where document like '{}';

# 删除语句
delete from langchain_pg_embedding where uuid='';
```