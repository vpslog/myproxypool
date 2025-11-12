from flask import Flask, request, jsonify, send_from_directory
from tinydb import TinyDB, Query
import asyncio
import aiohttp
import os
import threading
import time
import requests
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('data/.env')

app = Flask(__name__, static_folder='static')
db = TinyDB('data/db.json')
FREQUENCE = int(os.getenv("FREQUENCE", 60))
IPQS_KEY = os.getenv("IPQS_KEY")
TOKEN = os.getenv("TOKEN")
TEST_DOMAIN = os.getenv("TEST_DOMAIN", "cloudflare.com")
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
SERVER_IP = os.getenv("SERVER_IP")

# 启动时打印客户端安装命令
def print_client_installation_instructions():
    script_url = "https://raw.githubusercontent.com/vpslog/myproxypool/refs/heads/main/register_proxy.sh"
    print("\n--- Client Installation Instructions ---\n")
    print("Run the following command on your client machine:")
    print(f"""
bash <(curl -s {script_url}) {SERVER_IP} {TOKEN} {USERNAME} {PASSWORD}
    """)
    print("\n--- Using Instructions ---\n")
    print("Run the following command to get proxy list:")
    print(f"""
curl -X GET http://{SERVER_IP}:5000/proxies -H "Authorization: {TOKEN}" -H "Content-Type: application/json"
    """)


lock = threading.Lock()

def validate_token(token):
    return token == TOKEN

async def check_proxy(proxy_ip):
    """检查代理的可用性和延迟"""
    url = f"https://{TEST_DOMAIN}"
    start_time = time.time()
    proxy_url = f"http://{USERNAME}:{PASSWORD}@{proxy_ip}:3128"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=proxy_url, timeout=5) as response:
                if response.status == 200:
                    latency = time.time() - start_time
                    return {"available": True, "latency": latency}
    except Exception:
        pass
    return {"available": False, "latency": None}

def get_ip_info(ip):
    """获取 IP 地址的地理位置等信息"""
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}")
        return response.json()
    except Exception:
        return {}

def get_ip_quality(ip):
    """获取 IP 质量信息 (IPQS)"""
    if not IPQS_KEY:
        return {}
    try:
        response = requests.get(f"https://ipqualityscore.com/api/json/ip/{IPQS_KEY}/{ip}")
        return response.json()
    except Exception:
        return {}

@app.route('/')
def index():
    """提供前端页面"""
    return send_from_directory('static', 'index.html')


@app.route('/proxies', methods=['GET'])
def get_proxies():
    """获取代理列表"""
    if not validate_token(request.headers.get("Authorization")):
        return jsonify({"error": "Unauthorized"}), 403

    mode = request.args.get("mode", "url")
    count = int(request.args.get("count", 10))
    sort_by = request.args.get("sort_by", "latency")
    filters = request.args.get("filter", "")

    with lock:
        proxies = db.all()
        if filters:
            regions = filters.split(",")
            proxies = [p for p in proxies if p.get("info", {}).get("regionName") in regions]

        if sort_by in ["latency", "quality"]:
            proxies = sorted(proxies, key=lambda x: x.get(sort_by) or float('inf'))

        # proxies = proxies[:count]

    if mode == "url":
        return "\n".join([f"http://{USERNAME}:{PASSWORD}@{p['ip']}:3128" for p in proxies])
    return jsonify(proxies)

@app.route('/proxies', methods=['POST'])
def add_proxy():
    """添加代理"""
    if not validate_token(request.headers.get("Authorization")):
        return jsonify({"error": "Unauthorized"}), 403

    proxy_ip = request.json.get("ip")
    if not proxy_ip:
        return jsonify({"error": "Missing IP"}), 400

    with lock:
        if db.contains(Query().ip == proxy_ip):
            return jsonify({"message": "IP already exists"}), 200

        ip_info = get_ip_info(proxy_ip)
        ip_quality = get_ip_quality(proxy_ip) if IPQS_KEY else {}

        db.insert({
            "ip": proxy_ip,
            "info": ip_info,
            "quality": ip_quality,
            "last_checked": None,
            "available": None,
            "latency": None,
        })

    return jsonify({"message": "IP added successfully"}), 201

@app.route('/proxies/<ip>', methods=['DELETE'])
def delete_proxy(ip):
    """删除代理"""
    if not validate_token(request.headers.get("Authorization")):
        return jsonify({"error": "Unauthorized"}), 403

    with lock:
        db.remove(Query().ip == ip)

    return jsonify({"message": "Proxy deleted successfully"})

def proxy_checker_loop():
    """后台定时任务，检测代理 IP 状态"""
    while True:
        time.sleep(FREQUENCE)
        with lock:
            proxies = db.all()
        for proxy in proxies:
            result = asyncio.run(check_proxy(proxy["ip"]))
            with lock:
                db.update({
                    "available": result["available"],
                    "latency": result["latency"],
                    "last_checked": time.time(),
                }, Query().ip == proxy["ip"])

if __name__ == "__main__":
    # 启动后台检测线程
    print_client_installation_instructions()
    threading.Thread(target=proxy_checker_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000,debug=True)
