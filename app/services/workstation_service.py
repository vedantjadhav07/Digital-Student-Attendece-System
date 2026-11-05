import ipaddress
from app.extensions import db
from app.models import Laboratory, Workstation
from app.utils.security import generate_workstation_token
from app.services.audit_service import AuditService


class WorkstationService:
    @staticmethod
    def provision_lab_workstations(lab: Laboratory, capacity: int = None, admin_user_id: int = None):
        """
        Provision or align workstations for a laboratory matching its capacity.
        Computes IP addresses sequentially if ip_start is defined.
        """
        target_capacity = capacity or lab.default_capacity or 30
        existing_workstations = Workstation.query.filter_by(lab_id=lab.id).all()
        existing_seats = {ws.seat_number: ws for ws in existing_workstations}

        # Determine base IP if configured
        base_ip = None
        if lab.ip_start:
            try:
                base_ip = ipaddress.ip_address(lab.ip_start)
            except ValueError:
                pass

        created_count = 0
        for seat in range(1, target_capacity + 1):
            if seat not in existing_seats:
                # Compute IP
                ws_ip = None
                if base_ip:
                    try:
                        ws_ip = str(base_ip + (seat - 1))
                    except Exception:
                        pass

                code_prefix = lab.code or f"LAB{lab.id}"
                ws = Workstation(
                    lab_id=lab.id,
                    workstation_code=f"{code_prefix}-WS{seat:02d}",
                    seat_number=seat,
                    ip_address=ws_ip,
                    secret_token=generate_workstation_token(),
                    status='active'
                )
                db.session.add(ws)
                created_count += 1

        db.session.commit()
        if admin_user_id and created_count > 0:
            AuditService.log(
                action="WORKSTATIONS_PROVISIONED",
                user_id=admin_user_id,
                target_type="Laboratory",
                target_id=lab.id,
                details=f"Provisioned {created_count} workstations for {lab.name} (Capacity: {target_capacity})"
            )
        return created_count

    @staticmethod
    def find_workstation_for_request(lab_id: int, client_ip: str, token: str = None):
        """
        Find a workstation in the given lab matching:
        1. Token if provided, OR
        2. Exact IP address match in this lab, OR
        3. Match by PC host number ending in IP.
        """
        # 1. Try Token match
        if token:
            ws = Workstation.query.filter_by(lab_id=lab_id, secret_token=token, status='active').first()
            if ws:
                return ws

        # 2. Try exact registered IP match
        if client_ip:
            ws = Workstation.query.filter_by(lab_id=lab_id, ip_address=client_ip, status='active').first()
            if ws:
                return ws

            # 3. For development or localhost loopback, or LAN subnet match
            # If client_ip is 127.0.0.1 or test IP, find by seat calculation
            try:
                last_octet = int(client_ip.split('.')[-1])
                ws = Workstation.query.filter_by(lab_id=lab_id, seat_number=last_octet, status='active').first()
                if ws:
                    return ws
            except (ValueError, IndexError):
                pass

        return None

