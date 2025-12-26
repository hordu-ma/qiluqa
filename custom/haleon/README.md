# 开发环境部署命令
```
### 运行容器实例
docker run -m 512m --restart=always --privileged=true -itd -p8062:8063 -v/tmp:/nas -v/home/haleon-local-qa:/app/bespin-local-qa -w/app/bespin-local-qa/ \
 -e CONTENT_PATH="/app/bespin-local-qa/content/" \
 -e OPENAI_API_KEY="<OPENAI_API_KEY>" \
 -e NO_PROXY="*" \
 --name haleon-local-qa bespin/bot-py-api:20240130 \
 sh -c "python -u api.py 2>&1"
```

# 测试环境部署命令
```
### 本机执行命令
docker -H 47.236.254.2 build -t registry.cn-shanghai.aliyuncs.com/ai-copilot/ai-copilot-py:test .
### 44服务器上执行命令
docker login --username=lsy01426683@1862559946566560 registry.cn-shanghai.aliyuncs.com
docker push registry.cn-shanghai.aliyuncs.com/ai-copilot/ai-copilot-py:test
```

# 生产环境部署命令
```
### 本机执行命令
docker -H 47.236.254.2 build -t registry.cn-shanghai.aliyuncs.com/ai-copilot/ai-copilot-py:prod .
### 44服务器上执行命令
docker login --username=lsy01426683@1862559946566560 registry.cn-shanghai.aliyuncs.com
docker push registry.cn-shanghai.aliyuncs.com/ai-copilot/ai-copilot-py:prod
```