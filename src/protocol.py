# src/protocol.py
import json
import socket
import uuid
from datetime import datetime

PROTOCOL_VERSION = "v1"
MAX_MESSAGE_SIZE = 1_048_576  # 1 Mo

def build_message(msg_type: str, payload: dict, request_id: str = None) -> dict:
    return {
        "version": PROTOCOL_VERSION,
        "type": msg_type,
        "request_id": request_id or str(uuid.uuid4()),
        "sent_at": datetime.now().isoformat(),
        "payload": payload,
    }

def encode_message(msg: dict) -> bytes:
    line = json.dumps(msg, ensure_ascii=False, separators=(",", ":"))
    return (line + "\n").encode("utf-8")

def decode_message(raw: str) -> dict:
    stripped = raw.strip()
    if not stripped:
        raise ValueError("Message vide")
    return json.loads(stripped)

def recv_line(conn: socket.socket, buffer: bytearray, max_size: int = MAX_MESSAGE_SIZE) -> str:
    while True:
        newline_pos = buffer.find(b"\n")
        if newline_pos != -1:
            line = buffer[:newline_pos].decode("utf-8")
            del buffer[:newline_pos + 1]
            return line
        chunk = conn.recv(4096)
        if not chunk:
            if buffer:
                line = buffer[:].decode("utf-8")
                buffer.clear()
                return line
            return None
        buffer.extend(chunk)
        if len(buffer) > max_size:
            raise ValueError(f"Message trop volumineux (> {max_size} octets)")