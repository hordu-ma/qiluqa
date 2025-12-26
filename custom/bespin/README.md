# chatommi-local-qa 测试环境部署命令
```
### 运行容器实例
docker run -m 1024m --restart=always --privileged=true -itd -p8062:8063 -v/data/knowledge2:/knowledge -v/data/apps/chatomni-local-qa:/app/bespin-local-qa -w/app/bespin-local-qa/ \
 -e APPLICATION_ENV="test" \
 -e CONTENT_PATH="/knowledge/" \
 -e OPENAI_API_KEY="<OPENAI_API_KEY>" \
 -e NO_PROXY="*" \
 --name chatomni-local-qa bespin/bot-py-api:20241112 \
 sh -c "python -u api.py 2>&1"
```

# chatommi-local-qa 生产环境部署命令
```
### 运行容器实例
docker run -m 1024m --restart=always --privileged=true -itd -p8062:8063 -v/data/knowledge2:/knowledge -v/data/apps/chatomni-local-qa:/app/bespin-local-qa -w/app/bespin-local-qa/ \
 -e APPLICATION_ENV="prod" \
 -e CONTENT_PATH="/knowledge/" \
 -e OPENAI_API_KEY="<OPENAI_API_KEY>" \
 -e NO_PROXY="*" \
 --name chatomni-local-qa bespin/bot-py-api:20241112 \
 sh -c "python -u api.py 2>&1"
```