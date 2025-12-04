#!/bin/sh

# 获取输入参数
SERVERIP=$1
SERVERPORT=$2
SERVERTOKEN=$3
PROXY_USER=$4
PROXY_PASSWORD=$5

# 检查参数
if [ -z "$SERVERIP" ] || [ -z "$SERVERPORT" ] || [ -z "$SERVERTOKEN" ] || [ -z "$PROXY_USER" ] || [ -z "$PROXY_PASSWORD" ]; then
    echo "Usage: $0 <SERVER_IP> <SERVERPORT> <SERVER_TOKEN> <PROXY_USER> <PROXY_PASSWORD>"
    exit 1
fi

# 获取本机 IP
MYIP=$(curl -s myip.ipip.net | grep -oP '\d+\.\d+\.\d+\.\d+')

if [ -z "$MYIP" ]; then
    echo "Failed to retrieve public IP address."
    exit 1
fi

echo "Detected public IP: $MYIP"

# 检查 Docker 是否已安装
if ! command -v docker >/dev/null 2>&1
then
    # 使用 curl 下载并执行 Docker 安装脚本
    curl -fsSL https://get.docker.com | sudo sh

    # 启动 Docker 服务
    sudo systemctl start docker

    # 设置 Docker 开机自启动
    sudo systemctl enable docker
fi

# 检查是否存在名为 3proxy 的容器
EXISTS=$(docker ps -a --filter "name=^/3proxy$" --format '{{.Names}}' 2>/dev/null || true)

SKIP_CREATE=0
if [ -n "$EXISTS" ]; then
    # 如果是交互式终端，询问用户；否则默认不删除
    if [ -t 0 ]; then
        read -r -p "Detected container '3proxy' already exists, delete and recreate? [y/N]: " REPLY
    else
        REPLY="n"
    fi

    case "$REPLY" in
        [yY]|[yY][eE][sS])
            echo "Removing existing '3proxy' container..."
            if ! docker rm -f 3proxy >/dev/null 2>&1; then
                echo "Failed to remove existing 3proxy container."
                exit 1
            fi
            ;;
        *)
            echo "Keeping existing 3proxy container, skipping creation."
            SKIP_CREATE=1
            ;;
    esac
fi


# 启动 3proxy 容器
if [ "$SKIP_CREATE" -eq 0 ]; then
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
fi

# 提交代理 IP 到服务端
curl -X POST http://$SERVERIP:$SERVERPORT/proxies \
    -H "Authorization: $SERVERTOKEN" \
    -H "Content-Type: application/json" \
    -d "{\"ip\": \"$MYIP\"}"

if [ $? -ne 0 ]; then
    echo "Failed to register proxy IP with server."
    exit 1
fi

echo "Proxy IP registered successfully with server."
