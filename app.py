from flask import Flask, request

app = Flask(__name__)

def get_real_ip():
    """Lấy IP thật của client (kể cả khi có proxy/nginx/heroku)"""
    if request.headers.getlist("X-Forwarded-For"):
        # Lấy IP đầu tiên trong X-Forwarded-For
        ip = request.headers.getlist("X-Forwarded-For")[0].split(",")[0].strip()
    else:
        ip = request.remote_addr
    return ip

@app.route("/")
def index():
    ip = get_real_ip()
    return f"Xin chào! IP thật của bạn là: {ip}"

if __name__ == "__main__":
    # host=0.0.0.0 để server lắng nghe tất cả IP
    app.run(host="0.0.0.0", port=5000)
