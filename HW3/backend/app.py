from flask import Flask, jsonify, request
import os
import datetime
import socket

app = Flask(__name__)

@app.route('/')
def get_info():
    data = {
        "message": "Hello from Backend (кубер работает)!",
        "pod_hostname": os.environ.get('HOSTNAME', 'unknown'),
        "pod_ip": socket.gethostbyname(socket.gethostname()),
        "server_time_utc": datetime.datetime.utcnow().isoformat(),
        "forwarded_by_frontend": request.headers.get('X-Frontend-Proxy', 'false')
    }
    return jsonify(data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)