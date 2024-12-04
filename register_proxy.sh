#!/bin/sh

# 获取输入参数
SERVERIP=$1
SERVERTOKEN=$2
PROXY_USER=$3
PROXY_PASSWORD=$4

# 检查参数
if [ -z "$SERVERIP" ] || [ -z "$SERVERTOKEN" ] || [ -z "$PROXY_USER" ] || [ -z "$PROXY_PASSWORD" ]; then
    echo "Usage: $0 <SERVER_IP> <SERVER_TOKEN> <PROXY_USER> <PROXY_PASSWORD>"
    exit 1
fi

# 获取本机 IP
MYIP=$(curl -s myip.ipip.net | grep -oP '\d+\.\d+\.\d+\.\d+')

if [ -z "$MYIP" ]; then
    echo "Failed to retrieve public IP address."
    exit 1
fi

echo "Detected public IP: $MYIP"

# 启动 3proxy 容器
docker run -d --restart=always \
    -p "3128:3128/tcp" \
    -p "1080:1080/tcp" \
    -e "PROXY_LOGIN=$PROXY_USER" \
    -e "PROXY_PASSWORD=$PROXY_PASSWORD" \
    --name 3proxy \
    ghcr.io/tarampampam/3proxy:latest

if [ $? -ne 0 ]; then
    echo "Failed to start 3proxy container."
    exit 1
fi

echo "3proxy container started successfully."

# 提交代理 IP 到服务端
curl -X POST http://$SERVERIP:5000/add \
    -H "Authorization: $SERVERTOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"ip\": \"$MYIP\"}"

if [ $? -ne 0 ]; then
    echo "Failed to register proxy IP with server."
    exit 1
fi

echo "Proxy IP registered successfully with server."
