
## myproxypool

自建小型爬虫代理池。

### 服务端

基于 Tinydb 和 flask 构建。提供 API add/get 端口用于添加、获取代理节点。并在内部循环通过代理节点async请求 cloudflare.com 以获取服务器可用性、延迟。此外还能提供节点信息，请求 http://ip-api.com/json 获取 服务器的地址信息。如果提供了 IPQS_KEY，还可以通过 IPQS 接口 https://ipqualityscore.com/api/json/ip/<IPQS_KEY>/USER_IP_HERE 获取 IP 质量信息。由于 IPQS 接口有请求频率限制，默认只在新加入机器时请求一次。

配置文件.env：
# 循环检查频率
FREQUENCE=
# API KEY
IPQS_KEY=
# 用于前后端通讯的TOKEN
TOKEN
# 用于节点链接的 USERNAME 和 PASSWORD
USERNAME=
PASSWORD=
# 测试网站，例如你可以改成 baidu.com
TEST_DOMAIN=


#### 接口

\add 添加服务器（这里只添加IP）

\get 获取指定的链接 string。可以指定返回值模式（json/url），以及数量、排序（按IP质量/延迟），并且可以加入 filter，例如限定某些区域。

### 客户端

客户端使用 docker 运行 3proxy 容器

docker run -d --restart=always     -p "3128:3128/tcp"     -p "1080:1080/tcp"     -e "PROXY_LOGIN=<PROXY_USER>"     -e "PROXY_PASSWORD=<PROXY_PASSWORD>" --name 3proxy     ghcr.io/tarampampam/3proxy:latest



 docker run -p 5056:5056 -v /app/myproxypool:/app/data --name=myproxypool -d ghcr.io/vpslog/myproxypool:latest 