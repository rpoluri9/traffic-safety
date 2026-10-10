"""End-to-end tests: rules engine, API endpoints, safety scores."""
from app.core.rules import TelemetryInput, evaluate_telemetry, safety_score
from app.models.violation import Violation
from tests.conftest import auth_headers, make_driver, make_vehicle


def base_telemetry(**overrides):
    data = dict(
        speed=40, speed_limit=50, heading=90, road_direction=90,
        signal_state="green", at_intersection=False, phone_in_use=False,
        alcohol_level=0.0, seatbelt_on=True, lat=1.0, lng=2.0,
    )
    data.update(overrides)
    return TelemetryInput(driver_id=1, vehicle_id=1, **data)


def types_of(hits):
    return [h.violation_type for h in hits]


# ---------- Rules engine unit tests ----------

def test_overspeed_medium():
    hits = evaluate_telemetry(base_telemetry(speed=58, speed_limit=50))
    assert types_of(hits) == ["OVERSPEED"]
    assert hits[0].severity == "MEDIUM"


def test_overspeed_high():
    hits = evaluate_telemetry(base_telemetry(speed=70, speed_limit=50))
    assert types_of(hits) == ["OVERSPEED"]
    assert hits[0].severity == "HIGH"


def test_overspeed_critical():
    hits = evaluate_telemetry(base_telemetry(speed=90, speed_limit=50))
    assert types_of(hits) == ["OVERSPEED"]
    assert hits[0].severity == "CRITICAL"


def test_no_violation_at_or_below_limit():
    assert evaluate_telemetry(base_telemetry(speed=50, speed_limit=50)) == []
    assert evaluate_telemetry(base_telemetry(speed=30, speed_limit=50)) == []


def test_signal_cross_red_light():
    hits = evaluate_telemetry(base_telemetry(speed=40, signal_state="red", at_intersection=True))
    assert "SIGNAL_CROSS" in types_of(hits)
    assert hits[0].severity == "HIGH"


def test_no_signal_violation_green_or_stopped():
    assert "SIGNAL_CROSS" not in types_of(evaluate_telemetry(base_telemetry(speed=40, signal_state="green", at_intersection=True)))
    assert "SIGNAL_CROSS" not in types_of(evaluate_telemetry(base_telemetry(speed=40, signal_state="red", at_intersection=False)))
    assert "SIGNAL_CROSS" not in types_of(evaluate_telemetry(base_telemetry(speed=0, signal_state="red", at_intersection=True)))


def test_wrong_way_driving():
    hits = evaluate_telemetry(base_telemetry(speed=50, heading=270, road_direction=90))
    assert "WRONG_WAY" in types_of(hits)


def test_no_wrong_way_same_direction():
    assert "WRONG_WAY" not in types_of(evaluate_telemetry(base_telemetry(speed=50, heading=95, road_direction=90)))


def test_mobile_use_while_moving():
    hits = evaluate_telemetry(base_telemetry(speed=40, phone_in_use=True))
    assert "MOBILE_USE" in types_of(hits)


def test_no_mobile_violation_parked():
    assert "MOBILE_USE" not in types_of(evaluate_telemetry(base_telemetry(speed=0, phone_in_use=True)))


def test_drunk_drive_critical():
    hits = evaluate_telemetry(base_telemetry(alcohol_level=0.10))
    assert "DRUNK_DRIVE" in types_of(hits)
    assert [h for h in hits if h.violation_type == "DRUNK_DRIVE"][0].severity == "CRITICAL"


def test_no_drunk_violation_below_limit():
    assert "DRUNK_DRIVE" not in types_of(evaluate_telemetry(base_telemetry(alcohol_level=0.05)))


def test_seatbelt_off_while_moving():
    hits = evaluate_telemetry(base_telemetry(speed=40, seatbelt_on=False))
    assert "NO_SEATBELT" in types_of(hits)


def test_no_seatbelt_violation_when_on_or_slow():
    assert "NO_SEATBELT" not in types_of(evaluate_telemetry(base_telemetry(speed=40, seatbelt_on=True)))
    assert "NO_SEATBELT" not in types_of(evaluate_telemetry(base_telemetry(speed=5, seatbelt_on=False)))


def test_multiple_violations_at_once():
    hits = evaluate_telemetry(base_telemetry(speed=70, speed_limit=50, phone_in_use=True, seatbelt_on=False))
    assert set(types_of(hits)) == {"OVERSPEED", "MOBILE_USE", "NO_SEATBELT"}


def test_safety_score_math():
    assert safety_score([]) == 100
    assert safety_score(["MEDIUM"]) == 92
    assert safety_score(["CRITICAL", "HIGH", "MEDIUM", "LOW"]) == 100 - 25 - 15 - 8 - 3
    assert safety_score(["CRITICAL"] * 10) == 0  # floored


# ---------- API tests ----------

def test_api_requires_key(client, db):
    make_driver(db)
    r = client.get("/api/v1/drivers")
    assert r.status_code == 401
    r = client.get("/api/v1/drivers", headers=auth_headers())
    assert r.status_code == 200


def test_telemetry_creates_violation_and_alert(client, db):
    d = make_driver(db)
    v = make_vehicle(db, driver_id=d.id)
    payload = dict(driver_id=d.id, vehicle_id=v.id, speed=80, speed_limit=50,
                   heading=90, road_direction=90, signal_state="green",
                   at_intersection=False, phone_in_use=False, alcohol_level=0.0,
                   seatbelt_on=True, lat=1.0, lng=2.0)
    r = client.post("/api/v1/telemetry", json=payload, headers=auth_headers())
    assert r.status_code == 200
    body = r.json()
    assert len(body["violations"]) == 1
    assert body["violations"][0]["type"] == "OVERSPEED"
    assert body["violations"][0]["severity"] == "CRITICAL"
    assert len(body["alerts"]) == 1  # CRITICAL raises an alert
    assert db.query(Violation).count() == 1


def test_telemetry_clean_creates_nothing(client, db):
    d = make_driver(db)
    v = make_vehicle(db, driver_id=d.id)
    payload = dict(driver_id=d.id, vehicle_id=v.id, speed=40, speed_limit=50,
                   heading=90, road_direction=90, signal_state="green",
                   at_intersection=False, phone_in_use=False, alcohol_level=0.0,
                   seatbelt_on=True, lat=1.0, lng=2.0)
    r = client.post("/api/v1/telemetry", json=payload, headers=auth_headers())
    assert r.status_code == 200
    assert r.json() == {"violations": [], "alerts": []}


def test_telemetry_rejects_unknown_driver(client, db):
    make_driver(db)
    make_vehicle(db)
    payload = dict(driver_id=999, vehicle_id=1, speed=40)
    r = client.post("/api/v1/telemetry", json=payload, headers=auth_headers())
    assert r.status_code == 400


def test_trip_lifecycle_and_waypoints(client, db):
    d = make_driver(db)
    v = make_vehicle(db, driver_id=d.id)
    r = client.post("/api/v1/trips", json=dict(
        driver_id=d.id, vehicle_id=v.id,
        pickup_name="A", pickup_lat=10.0, pickup_lng=20.0,
        dropoff_name="B", dropoff_lat=11.0, dropoff_lng=21.0,
    ), headers=auth_headers())
    assert r.status_code == 201
    trip = r.json()
    assert trip["status"] == "PLANNED"
    import json as _json
    waypoints = _json.loads(trip["waypoints"])
    assert len(waypoints) == 11
    assert waypoints[0] == [10.0, 20.0]
    assert waypoints[-1] == [11.0, 21.0]

    r = client.post(f"/api/v1/trips/{trip['id']}/start", headers=auth_headers())
    assert r.json()["status"] == "ACTIVE"
    r = client.post(f"/api/v1/trips/{trip['id']}/complete", headers=auth_headers())
    assert r.json()["status"] == "COMPLETED"
    # cannot complete twice
    r = client.post(f"/api/v1/trips/{trip['id']}/complete", headers=auth_headers())
    assert r.status_code == 400


def test_violations_filter_by_type(client, db):
    d = make_driver(db)
    v = make_vehicle(db, driver_id=d.id)
    for speed, phone in [(80, False), (40, True)]:
        client.post("/api/v1/telemetry", json=dict(
            driver_id=d.id, vehicle_id=v.id, speed=speed, speed_limit=50,
            heading=90, road_direction=90, signal_state="green", at_intersection=False,
            phone_in_use=phone, alcohol_level=0.0, seatbelt_on=True, lat=0, lng=0,
        ), headers=auth_headers())
    r = client.get("/api/v1/violations?type=MOBILE_USE", headers=auth_headers())
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["type"] == "MOBILE_USE"
    r = client.get("/api/v1/violations?severity=CRITICAL", headers=auth_headers())
    assert len(r.json()) == 1


def test_driver_safety_score_endpoint(client, db):
    d = make_driver(db)
    v = make_vehicle(db, driver_id=d.id)
    client.post("/api/v1/telemetry", json=dict(
        driver_id=d.id, vehicle_id=v.id, speed=80, speed_limit=50,
        heading=90, road_direction=90, signal_state="green", at_intersection=False,
        phone_in_use=False, alcohol_level=0.0, seatbelt_on=True, lat=0, lng=0,
    ), headers=auth_headers())
    r = client.get(f"/api/v1/drivers/{d.id}/safety-score", headers=auth_headers())
    assert r.status_code == 200
    body = r.json()
    assert body["safety_score"] == 75  # 100 - 25 (CRITICAL)
    assert body["violation_count"] == 1


def test_alert_acknowledge(client, db):
    d = make_driver(db)
    v = make_vehicle(db, driver_id=d.id)
    res = client.post("/api/v1/telemetry", json=dict(
        driver_id=d.id, vehicle_id=v.id, speed=80, speed_limit=50,
        heading=90, road_direction=90, signal_state="green", at_intersection=False,
        phone_in_use=False, alcohol_level=0.0, seatbelt_on=True, lat=0, lng=0,
    ), headers=auth_headers()).json()
    alert_id = res["alerts"][0]["id"]
    r = client.post(f"/api/v1/alerts/{alert_id}/acknowledge", headers=auth_headers())
    assert r.json()["acknowledged"] is True
    r = client.get("/api/v1/alerts?unacknowledged_only=true", headers=auth_headers())
    assert r.json() == []


def test_dashboard_stats(client, db):
    d = make_driver(db)
    v = make_vehicle(db, driver_id=d.id)
    client.post("/api/v1/telemetry", json=dict(
        driver_id=d.id, vehicle_id=v.id, speed=80, speed_limit=50,
        heading=90, road_direction=90, signal_state="green", at_intersection=False,
        phone_in_use=False, alcohol_level=0.0, seatbelt_on=True, lat=0, lng=0,
    ), headers=auth_headers())
    r = client.get("/api/v1/dashboard/stats", headers=auth_headers())
    assert r.status_code == 200
    body = r.json()
    assert body["total_violations"] == 1
    assert body["critical_alerts"] == 1
    assert body["by_type"]["OVERSPEED"] == 1
    assert body["by_severity"]["CRITICAL"] == 1


def test_dashboard_page_renders(client, db):
    r = client.get("/")
    assert r.status_code == 200
    assert "Traffic Safety Monitor" in r.text
