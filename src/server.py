import socket
import logging
import argparse
import time
import os
import json

from src.models import IngestRequest, IngestResponse, SensorReading
from src.validators import validate_readings
from src.protocol import recv_line, decode_message, encode_message, build_message

# --- Logs ---
os.makedirs("logs", exist_ok=True)
logger = logging.getLogger("smartfarm.server")
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
file_handler = logging.FileHandler("logs/server.log", mode="a", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# --- Partie actionneurs ---
ACTIONNEUR_HOST = "127.0.0.1"
ACTIONNEUR_PORT = 9001

def compute_actions(reading: SensorReading):
    """Simule les actions pour une lecture donnée."""
    actions = []

    # Vérifier l'humidité et la pompe
    if hasattr(reading, "humidity") and reading.humidity is not None:
        if reading.humidity < 30 and getattr(reading, "pump_status", "OFF") != "ON":
            actions.append("turn_on_pump")

    # Vérifier la température et le ventilateur
    if hasattr(reading, "temperature") and reading.temperature is not None:
        if reading.temperature > 35:
            actions.append("turn_on_fan")

    return actions

def send_actions_to_actuator(actions: list):
    """Envoie les actions simulées à l'actionneur via socket."""
    if not actions:
        return
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ACTIONNEUR_HOST, ACTIONNEUR_PORT))
            s.sendall(json.dumps(actions).encode("utf-8"))
    except ConnectionRefusedError:
        logger.warning("Impossible de joindre l'actionneur sur %s:%d", ACTIONNEUR_HOST, ACTIONNEUR_PORT)

# --- Gestion client ---
def handle_client(conn: socket.socket, addr: tuple):
    """Traite une connexion client unique."""
    buffer = bytearray()
    request_id = "unknown"
    start_time = time.time()

    try:
        conn.settimeout(30.0)
        line = recv_line(conn, buffer)
        if line is None:
            logger.warning("Connexion fermée immédiatement par %s", addr)
            return

        msg = decode_message(line)
        request_id = msg.get("request_id", "unknown")
        msg_type = msg.get("type", "")
        logger.info("[%s] Message reçu : type=%s depuis %s", request_id, msg_type, addr)

        if msg_type != "ingest_request":
            error_resp = build_message("error",
                {"message": f"Type non supporté : {msg_type}"},
                request_id=request_id)
            conn.sendall(encode_message(error_resp))
            return

        payload = msg.get("payload", {})
        ingest_req = IngestRequest.from_dict(payload)
        logger.info("[%s] %d lectures à valider (source=%s)",
                    request_id, len(ingest_req.readings), ingest_req.source)

        accepted, errors = validate_readings(ingest_req.readings)

        # --- Application des actionneurs simulés ---
        for r in accepted:
            r.actions = compute_actions(r)
            if r.actions:
                logger.info("[%s] Actions simulées pour %s : %s",
                            request_id, r.sensor_id, r.actions)
                send_actions_to_actuator(r.actions)

        elapsed_ms = (time.time() - start_time) * 1000
        response = IngestResponse(
            request_id=request_id,
            accepted_count=len(accepted),
            rejected_count=len(errors),
            errors=errors,
            processing_time_ms=round(elapsed_ms, 2),
        )

        resp_msg = build_message("ingest_response",
                                 response.to_dict(),
                                 request_id=request_id)
        conn.sendall(encode_message(resp_msg))

        logger.info("[%s] Réponse envoyée : accepted=%d, rejected=%d, time=%.2fms",
                    request_id, response.accepted_count,
                    response.rejected_count, elapsed_ms)

    except socket.timeout:
        logger.error("[%s] Timeout client %s", request_id, addr)
    except (ValueError, KeyError) as e:
        logger.error("[%s] Erreur de parsing : %s", request_id, e)
        try:
            err_msg = build_message("error",
                {"message": str(e)}, request_id=request_id)
            conn.sendall(encode_message(err_msg))
        except OSError:
            pass
    except OSError as e:
        logger.error("[%s] Erreur réseau : %s", request_id, e)
    finally:
        conn.close()

# --- Serveur principal ---
def run_server(host: str = "127.0.0.1", port: int = 9000):
    """Lance le serveur TCP."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((host, port))
        srv.listen(5)
        logger.info("🚀 Serveur en écoute sur %s:%d", host, port)

        while True:
            try:
                conn, addr = srv.accept()
                logger.info("Connexion acceptée depuis %s:%d", addr[0], addr[1])
                handle_client(conn, addr)
            except KeyboardInterrupt:
                logger.info("Arrêt du serveur (Ctrl+C)")
                break
            except OSError as e:
                logger.error("Erreur accept : %s", e)

# --- Point d'entrée ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Serveur d'ingestion IoT")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    args = parser.parse_args()
    run_server(args.host, args.port)