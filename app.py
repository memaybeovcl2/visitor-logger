from flask import Flask, request
import datetime

app = Flask(__name__)

def get_client_ip():
    """Lấy IP thật từ header hoặc remote_addr"""
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
    else:
        ip = request.remote_addr
    return ip

def log_visitor(ip, user_agent, path):
    """Ghi thông tin truy cập vào file log"""
    with open("visitors.log", "a", encoding="utf-8") as f:
        time_now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{time_now}] IP={ip} | Path={path} | UA={user_agent}\n")

@app.route("/", methods=["GET"])
def home():
    ip = get_client_ip()
    user_agent = request.headers.get("User-Agent", "Unknown")
    path = request.path

    log_visitor(ip, user_agent, path)

    return f"""
    <h2>Xin chào!</h2>
    <p>IP của bạn: <b>{ip}</b></p>
    <p>User-Agent: {user_agent}</p>
    """

@app.route("/log", methods=["GET"])
def show_log():
    """Xem log ngay trên web"""
    try:
        with open("visitors.log", "r", encoding="utf-8") as f:
            content = f.read().replace("\n", "<br>")
    except FileNotFoundError:
        content = "Chưa có log nào."
    return f"<h3>Visitor Log</h3><p>{content}</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
