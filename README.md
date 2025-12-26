# 文档
## 项目介绍
大模型本地知识库主工程

## 项目结构
* bespin-local-qa        [**根目录**]
  * config               [**配置文件**]
    * prod               [**生产环境配置**]
    * test               [**测试环境配置**]
  * content              [**文本目录**]
  * custom               [**定制目录**]
  * framework            [**框架配置**]
    * redis              [**Redis配置目录**]
    * static             [**SwaggerUI配置目录**]
    * util               [**工具包**]
  * log                  [**日志目录**]
  * models               [**模型目录**]
    * chains             [**链式服务**]
    * embeddings         [**Embedding服务**]
    * llms               [**大语言模型服务**] 
    * vectordatabase     [**向量库服务**]
  * service              [**通用业务**]
    * domain             [**领域对象**]
    * namespacefile      [**知识文件领域**]
  * api.py               [**API服务启动程序**]
  * README.md            [**说明文档**]
  * pyproject.toml       [**uv 依赖声明**]
  * uv.lock              [**uv 锁文件**]


## 依赖管理（uv）
```
# 初始化/创建虚拟环境并安装依赖（在本目录执行）
uv sync

# 添加依赖（写入 pyproject.toml 并更新 uv.lock）
uv add <package>

# 删除依赖
uv remove <package>

# 更新锁文件（一般 add/remove 会自动更新）
uv lock
```

## 部署指引
### 1.离线镜像部署
```
# 容器打包
docker commit [CONTAINER_ID] bespin/bot-py-api:latest
# 镜像打包
docker save -o bot-py-api.tar bespin/bot-py-api:latest
# 导入镜像
docker load < /bot-py-api.tar
```

### 测试环境部署命令
```
docker -H 192.168.191.44 build -t registry.cn-shanghai.aliyuncs.com/ai-copilot/ai-copilot-py:test .
docker -H 192.168.191.44 login --username=lsy01426683@1862559946566560 registry.cn-shanghai.aliyuncs.com
docker -H 192.168.191.44 push registry.cn-shanghai.aliyuncs.com/ai-copilot/ai-copilot-py:test
```
