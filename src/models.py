from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class SensorReading:
    """Lecture d'un capteur IoT selon le TP intégré SmartFarm"""
    request_id: str
    timestamp: str
    sensor_id: str
    site_id: str
    temperature: float
    humidity: float
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    ozone: Optional[float] = None
    no2: Optional[float] = None
    irrigation: str = "OFF"  # ON / OFF
    battery: Optional[int] = None

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            request_id=d.get("request_id", ""),
            timestamp=d.get("timestamp", ""),
            sensor_id=d.get("sensor_id", ""),
            site_id=d.get("site_id", ""),
            temperature=d.get("temperature", 0.0),
            humidity=d.get("humidity", 0.0),
            pm25=d.get("pm25"),
            pm10=d.get("pm10"),
            ozone=d.get("ozone"),
            no2=d.get("no2"),
            irrigation=d.get("irrigation", "OFF"),
            battery=d.get("battery")
        )


@dataclass
class ValidationError:
    sensor_id: str
    field: str
    message: str

    def to_dict(self):
        return self.__dict__


@dataclass
class IngestRequest:
    source: str
    readings: List[SensorReading]

    def to_dict(self):
        return {
            "source": self.source,
            "readings": [r.to_dict() for r in self.readings]
        }

    @classmethod
    def from_dict(cls, d: dict):
        readings = [SensorReading.from_dict(r) for r in d.get("readings", [])]
        return cls(source=d.get("source", ""), readings=readings)


@dataclass
class IngestResponse:
    request_id: str
    accepted_count: int
    rejected_count: int
    errors: List[ValidationError] = field(default_factory=list)
    processing_time_ms: float = 0.0

    def to_dict(self):
        return {
            "request_id": self.request_id,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "errors": [e.to_dict() for e in self.errors],
            "processing_time_ms": self.processing_time_ms,
        }