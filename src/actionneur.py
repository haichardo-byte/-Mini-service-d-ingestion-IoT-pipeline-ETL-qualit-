# actionneur.py
import socket
import json

HOST = "127.0.0.1"
PORT = 9001

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"🚀 Actionneur en écoute sur {HOST}:{PORT}")

    while True:
        conn, addr = s.accept()
        with conn:
            data = conn.recv(4096)
            if data:
                try:
                    msg = json.loads(data.decode("utf-8"))
                    print("🔔 Actions reçues :", msg)
                except json.JSONDecodeError:
                    print("⚠️ Message invalide :", data)