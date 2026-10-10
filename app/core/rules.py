"""Rules engine: pure threshold-based driving-safety checks.

Every rule is a plain function over telemetry values — no machine learning,
no statistics, no external services. A violation fires when a sensor reading
crosses a fixed, documented threshold.
"""
from dataclasses import dataclass, field

# --- Thresholds (all in plain units, documented for the demo) ---
SPEED_MARGIN_MEDIUM = 10.0   # km/h over the limit -> MEDIUM overspeed
SPEED_MARGIN_HIGH = 25.0     # km/h over the limit -> HIGH overspeed (above: CRITICAL)
MOVING_SPEED = 5.0           # km/h: above this the vehicle counts as moving
SEATBELT_MIN_SPEED = 10.0    # km/h: seatbelt required above this speed
WRONG_WAY_MIN_SPEED = 10.0  # km/h: wrong-way checked above this speed
WRONG_WAY_ANGLE = 90.0       # degrees: heading this far off road direction = wrong way
ALCOHOL_LIMIT = 0.08         # BAC: above this = drunk driving (CRITICAL)

# Safety-score penalty weights per severity
SCORE_PENALTIES = {"LOW": 3, "MEDIUM": 8, "HIGH": 15, "CRITICAL": 25}


@dataclass
class TelemetryInput:
    driver_id: int
    vehicle_id: int
    trip_id: int | None = None
    speed: float = 0.0            # km/h
    speed_limit: float = 50.0     # km/h, limit of the current road
    heading: float = 0.0          # degrees 0-359, direction of travel
    road_direction: float = 0.0   # degrees 0-359, legal direction of the road
    signal_state: str = "green"   # red | yellow | green
    at_intersection: bool = False
    phone_in_use: bool = False
    alcohol_level: float = 0.0    # blood alcohol content
    seatbelt_on: bool = True
    lat: float = 0.0
    lng: float = 0.0


@dataclass
class RuleHit:
    violation_type: str
    severity: str
    message: str
    speed: float = 0.0
    speed_limit: float | None = None
    lat: float = 0.0
    lng: float = 0.0
    extra: dict = field(default_factory=dict)


def _angular_difference(a: float, b: float) -> float:
    """Smallest angle between two headings, 0..180 degrees."""
    return abs((a - b + 180) % 360 - 180)


def check_overspeed(t: TelemetryInput) -> RuleHit | None:
    margin = t.speed - t.speed_limit
    if margin <= 0:
        return None
    if margin <= SPEED_MARGIN_MEDIUM:
        severity = "MEDIUM"
    elif margin <= SPEED_MARGIN_HIGH:
        severity = "HIGH"
    else:
        severity = "CRITICAL"
    return RuleHit(
        violation_type="OVERSPEED",
        severity=severity,
        message=f"Speed {t.speed:.0f} km/h in a {t.speed_limit:.0f} km/h zone "
                f"(+{margin:.0f} over limit)",
        speed=t.speed,
        speed_limit=t.speed_limit,
        lat=t.lat,
        lng=t.lng,
    )


def check_signal_cross(t: TelemetryInput) -> RuleHit | None:
    if t.signal_state == "red" and t.at_intersection and t.speed > MOVING_SPEED:
        return RuleHit(
            violation_type="SIGNAL_CROSS",
            severity="HIGH",
            message=f"Crossed intersection on red signal at {t.speed:.0f} km/h",
            speed=t.speed,
            lat=t.lat,
            lng=t.lng,
        )
    return None


def check_wrong_way(t: TelemetryInput) -> RuleHit | None:
    if t.speed > WRONG_WAY_MIN_SPEED and _angular_difference(t.heading, t.road_direction) > WRONG_WAY_ANGLE:
        return RuleHit(
            violation_type="WRONG_WAY",
            severity="HIGH",
            message=f"Driving against road direction "
                    f"(heading {t.heading:.0f}°, road {t.road_direction:.0f}°)",
            speed=t.speed,
            lat=t.lat,
            lng=t.lng,
        )
    return None


def check_mobile_use(t: TelemetryInput) -> RuleHit | None:
    if t.phone_in_use and t.speed > MOVING_SPEED:
        return RuleHit(
            violation_type="MOBILE_USE",
            severity="MEDIUM",
            message=f"Phone in use while driving at {t.speed:.0f} km/h",
            speed=t.speed,
            lat=t.lat,
            lng=t.lng,
        )
    return None


def check_drunk_drive(t: TelemetryInput) -> RuleHit | None:
    if t.alcohol_level > ALCOHOL_LIMIT:
        return RuleHit(
            violation_type="DRUNK_DRIVE",
            severity="CRITICAL",
            message=f"Alcohol level {t.alcohol_level:.3f} BAC above legal limit {ALCOHOL_LIMIT}",
            speed=t.speed,
            lat=t.lat,
            lng=t.lng,
            extra={"alcohol_level": t.alcohol_level},
        )
    return None


def check_seatbelt(t: TelemetryInput) -> RuleHit | None:
    if not t.seatbelt_on and t.speed > SEATBELT_MIN_SPEED:
        return RuleHit(
            violation_type="NO_SEATBELT",
            severity="MEDIUM",
            message=f"Seatbelt off while driving at {t.speed:.0f} km/h",
            speed=t.speed,
            lat=t.lat,
            lng=t.lng,
        )
    return None


RULES = [
    check_overspeed,
    check_signal_cross,
    check_wrong_way,
    check_mobile_use,
    check_drunk_drive,
    check_seatbelt,
]


def evaluate_telemetry(t: TelemetryInput) -> list[RuleHit]:
    """Run every rule over one telemetry reading; return all violations found."""
    hits: list[RuleHit] = []
    for rule in RULES:
        hit = rule(t)
        if hit is not None:
            hits.append(hit)
    return hits


def safety_score(penalties: list[str]) -> int:
    """100 minus weighted penalties, floored at 0."""
    total = sum(SCORE_PENALTIES.get(p, 0) for p in penalties)
    return max(0, 100 - total)
