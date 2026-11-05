from app.models import Laboratory, Workstation
from app.services.workstation_service import WorkstationService
from app.utils.network import is_ip_in_range, is_ip_in_subnet


def test_ip_range_validation():
    assert is_ip_in_range("192.168.1.15", "192.168.1.1", "192.168.1.30") is True
    assert is_ip_in_range("192.168.1.1", "192.168.1.1", "192.168.1.30") is True
    assert is_ip_in_range("192.168.1.30", "192.168.1.1", "192.168.1.30") is True
    assert is_ip_in_range("192.168.1.31", "192.168.1.1", "192.168.1.30") is False
    assert is_ip_in_range("10.0.0.5", "192.168.1.1", "192.168.1.30") is False


def test_subnet_validation():
    assert is_ip_in_subnet("192.168.1.55", "192.168.1.0/24") is True
    assert is_ip_in_subnet("192.168.2.55", "192.168.1.0/24") is False


def test_workstation_provisioning(db):
    lab = Laboratory(name="Test Lab A", code="TLA", ip_start="10.0.1.1", default_capacity=30)
    db.session.add(lab)
    db.session.commit()

    created = WorkstationService.provision_lab_workstations(lab, capacity=30)
    assert created == 30

    workstations = Workstation.query.filter_by(lab_id=lab.id).order_by(Workstation.seat_number.asc()).all()
    assert len(workstations) == 30
    assert workstations[0].workstation_code == "TLA-WS01"
    assert workstations[0].ip_address == "10.0.1.1"
    assert workstations[29].workstation_code == "TLA-WS30"
    assert workstations[29].ip_address == "10.0.1.30"
    assert workstations[0].secret_token is not None


def test_find_workstation(db, test_lab):
    # Find by exact IP
    ws = WorkstationService.find_workstation_for_request(lab_id=test_lab.id, client_ip="192.168.1.5")
    assert ws is not None
    assert ws.seat_number == 5

    # Find by token
    token = ws.secret_token
    ws_by_token = WorkstationService.find_workstation_for_request(lab_id=test_lab.id, client_ip="10.0.0.1", token=token)
    assert ws_by_token is not None
    assert ws_by_token.id == ws.id

