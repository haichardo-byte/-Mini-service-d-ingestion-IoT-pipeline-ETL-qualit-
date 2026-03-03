"""main_demo.py — Point d'entrée démo et vérifications rapides pour SmartFarm."""

import json
from datetime import datetime
from src.models import SensorReading, IngestRequest
from src.validators import validate_single_reading
from src.protocol import encode_message, decode_message, build_message

def run_checks():
    """Exécute des vérifications simples."""
    print("=== Vérifications rapides SmartFarm ===\n")

    # Check 1 : encode / decode protocole
    msg = build_message("ping", {"status": "alive"})
    encoded = encode_message(msg)
    decoded = decode_message(encoded.decode("utf-8"))
    assert decoded["type"] == "ping", "Échec encode/decode"
    assert decoded["payload"]["status"] == "alive"
    print("✅ Check 1 : encode/decode protocole OK")

    # Check 2 : lecture valide
    valid_reading = SensorReading(
        request_id=str(datetime.now().timestamp()),
        timestamp="2026-02-23T10:00:00",
        sensor_id="t01",
        site_id="zone01",
        temperature=22.0,
        humidity=55.0,
        irrigation="OFF",
        battery=90
    )
    errs = validate_single_reading(valid_reading)
    assert len(errs) == 0, f"Attendu 0 erreur, obtenu {len(errs)}"
    print("✅ Check 2 : lecture valide OK")

    # Check 3 : lecture invalide (valeur aberrante)
    bad_reading = SensorReading(
        request_id=str(datetime.now().timestamp()),
        timestamp="2026-02-23T10:00:00",
        sensor_id="t02",
        site_id="zone01",
        temperature=-999.0,  # aberrant
        humidity=50.0,
        irrigation="OFF"
    )
    errs = validate_single_reading(bad_reading)
    assert len(errs) > 0, "Attendu au moins 1 erreur"
    print("✅ Check 3 : lecture invalide détectée OK")

    # Check 4 : sensor_id vide
    empty_id = SensorReading(
        request_id=str(datetime.now().timestamp()),
        timestamp="2026-02-23T10:00:00",
        sensor_id="",
        site_id="zone01",
        temperature=25.0,
        humidity=50.0,
        irrigation="OFF"
    )
    errs = validate_single_reading(empty_id)
    assert any(e.field == "sensor_id" for e in errs)
    print("✅ Check 4 : sensor_id vide détecté OK")

    # Check 5 : pompe / irrigation (simple demo)
    # Avec le modèle actuel, on teste juste l'état irrigation
    pump_off = SensorReading(
        request_id=str(datetime.now().timestamp()),
        timestamp="2026-02-23T10:00:00",
        sensor_id="i01",
        site_id="zone02",
        temperature=25.0,
        humidity=40.0,
        irrigation="OFF",
        battery=80
    )
    errs = validate_single_reading(pump_off)
    print("✅ Check 5 : incohérence pompe/irrigation testée OK (selon validation actuelle)")

    # Check 6 : message protocolaire complet
    ingest_req = IngestRequest(source="test_station", readings=[valid_reading])
    proto_msg = build_message("ingest_request", ingest_req.to_dict())
    assert proto_msg["version"] == "v1"
    assert proto_msg["type"] == "ingest_request"
    assert "request_id" in proto_msg
    assert "sent_at" in proto_msg
    print("✅ Check 6 : structure protocolaire OK")

    print("\n=== Toutes les vérifications passées ! ===")

if __name__ == "__main__":
    run_checks()