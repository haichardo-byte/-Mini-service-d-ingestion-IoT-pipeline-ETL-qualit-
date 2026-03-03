import socket
import json
import logging
import argparse
import time
import os

from src.models import IngestRequest, SensorReading
from src.protocol import encode_message, recv_line, decode_message, build_message

os.makedirs("logs", exist_ok=True)
logger = logging.getLogger("smartfarm.client")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s",
                              datefmt="%Y-%m-%d %H:%M:%S")
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
file_handler = logging.FileHandler("logs/client.log", mode="a", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


def load_readings(filepath: str) -> list[dict]:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def send_ingest_request(host: str, port: int, request_msg: dict,
                        timeout: float = 10.0) -> dict | None:
    request_id = request_msg.get("request_id", "?")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            logger.info("[%s] Connexion à %s:%d …", request_id, host, port)
            sock.connect((host, port))

            payload_bytes = encode_message(request_msg)
            sock.sendall(payload_bytes)
            logger.info("[%s] Requête envoyée (%d octets)", request_id, len(payload_bytes))

            buffer = bytearray()
            line = recv_line(sock, buffer)
            if line is None:
                logger.error("[%s] Pas de réponse du serveur", request_id)
                return None

            response = decode_message(line)
            logger.info("[%s] Réponse reçue : type=%s", request_id, response.get("type"))
            return response

    except socket.timeout:
        logger.error("[%s] ⏱ Timeout", request_id)
    except ConnectionRefusedError:
        logger.error("[%s] 🚫 Connexion refusée", request_id)
    except ConnectionResetError:
        logger.error("[%s] 💥 Connexion réinitialisée", request_id)
    except OSError as e:
        logger.error("[%s] Erreur réseau : %s", request_id, e)
    return None


def display_response(response: dict):
    payload = response.get("payload", {})
    print("\n" + "=" * 50)
    print("  RÉSULTAT D'INGESTION")
    print("=" * 50)
    print(f"  Request ID   : {payload.get('request_id', '?')}")
    print(f"  Acceptées    : {payload.get('accepted_count', 0)}")
    print(f"  Rejetées     : {payload.get('rejected_count', 0)}")
    print(f"  Temps (ms)   : {payload.get('processing_time_ms', 0):.2f}")

    errors = payload.get("errors", [])
    if errors:
        print(f"\n  Erreurs de validation ({len(errors)}) :")
        for err in errors:
            print(f"    - [{err['sensor_id']}] {err['field']} : {err['message']}")
    print("=" * 50 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Client d'ingestion IoT")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    parser.add_argument("--data", default="data/rawdata.json")
    parser.add_argument("--interval", type=int, default=5,
                        help="Intervalle entre envois (secondes)")
    args = parser.parse_args()

    logger.info("🚀 Client démarré en mode flux continu (interval=%ss)", args.interval)

    while True:
        raw_readings = load_readings(args.data)
        readings = [SensorReading.from_dict(r) for r in raw_readings]

        ingest_req = IngestRequest(source="station_agri_01", readings=readings)
        msg = build_message("ingest_request", ingest_req.to_dict())
        request_id = msg["request_id"]

        logger.info("[%s] %d lectures chargées", request_id, len(readings))

        start = time.time()
        response = send_ingest_request(args.host, args.port, msg)
        elapsed = (time.time() - start) * 1000

        if response:
            display_response(response)
            logger.info("[%s] Échange complet en %.2fms", request_id, elapsed)
        else:
            logger.error("[%s] Échec de l'échange", request_id)

        time.sleep(args.interval)


if __name__ == "__main__":
    main()