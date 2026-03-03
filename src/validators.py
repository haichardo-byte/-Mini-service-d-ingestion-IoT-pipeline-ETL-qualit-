from datetime import datetime
from typing import List, Tuple
import logging

from src.models import SensorReading, ValidationError

logger = logging.getLogger("ingestion.validator")

def validate_single_reading(r: SensorReading) -> List[ValidationError]:
    errors = []

    # sensor_id et site_id obligatoires
    if not r.sensor_id.strip():
        errors.append(ValidationError(r.sensor_id, "sensor_id", "Obligatoire"))
    if not r.site_id.strip():
        errors.append(ValidationError(r.sensor_id, "site_id", "Obligatoire"))

    # temperature & humidity
    if not (-50 <= r.temperature <= 60):
        errors.append(ValidationError(r.sensor_id, "temperature", f"Hors plage [-50,60]"))
    if not (0 <= r.humidity <= 100):
        errors.append(ValidationError(r.sensor_id, "humidity", f"Hors plage [0,100]"))

    # irrigation normalisée
    if r.irrigation.upper() not in ["ON","OFF"]:
        errors.append(ValidationError(r.sensor_id, "irrigation", "Valeur ON/OFF attendue"))

    # timestamp valide
    try:
        datetime.fromisoformat(r.timestamp)
    except:
        errors.append(ValidationError(r.sensor_id, "timestamp", "Format ISO attendu"))

    return errors


def validate_readings(readings: List[SensorReading]) -> Tuple[List[SensorReading], List[ValidationError]]:
    accepted, all_errors = [], []
    for r in readings:
        errs = validate_single_reading(r)
        if errs:
            all_errors.extend(errs)
            logger.warning(f"Lecture rejetée [{r.sensor_id}] {len(errs)} erreur(s)")
        else:
            accepted.append(r)
    logger.info(f"Validation terminée : {len(accepted)} acceptées, {len(all_errors)} erreurs")
    return accepted, all_errors