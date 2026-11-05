import ipaddress
import secrets
from app.extensions import db
from app.models import Laboratory, Workstation
from app.utils.security import generate_workstation_token
from app.services.audit_service import AuditService


class WorkstationService:
    @staticmethod
    def generate_sequential_ip(base_ip_str: str, seat: int) -> str:
        """
        Generate sequential IP address by changing the last octet.
        For example:
        If admin enters '127.0.0.1' and capacity 30:
        Seat 1 -> 127.0.0.1
        Seat 2 -> 127.0.0.2
        ...
        Seat 30 -> 127.0.0.30
        """
        if not base_ip_str:
            return None
        try:
            parts = base_ip_str.strip().split('.')
            if len(parts) == 4:
                prefix = ".".join(parts[:3])
                last_octet = int(parts[3]) + (seat - 1)
                return f"{prefix}.{last_octet}"
            ip = ipaddress.ip_address(base_ip_str.strip())
            return str(ip + (seat - 1))
        except Exception:
            return None

    @staticmethod
    def generate_mac_address(lab_id: int, seat: int, lab_code: str = "") -> str:
        """
        Generate a unique, valid registered MAC address (format: XX:XX:XX:XX:XX:XX)
        using locally administered unicast range (02:...).
        """
        code_clean = (lab_code or f"L{lab_id}").strip()
        ch = sum(ord(c) for c in code_clean) % 256
        return f"02:{ch:02X}:{lab_id % 256:02X}:{(seat >> 8) & 0xFF:02X}:{seat % 256:02X}:{(seat * 7 + 13) % 256:02X}"

    @staticmethod
    def generate_device_id(lab_code: str, seat: int) -> str:
        """
        Generate a unique registered hardware/device ID token.
        e.g. DEV-ACL01-PC01-B3D9A102
        """
        code_prefix = "".join(filter(str.isalnum, (lab_code or "LAB"))).upper()
        rand_hex = secrets.token_hex(4).upper()
        return f"DEV-{code_prefix}-PC{seat:02d}-{rand_hex}"

    @staticmethod
    def provision_lab_workstations(lab: Laboratory, capacity: int = None, admin_user_id: int = None):
        """
        Provision or align workstations for a laboratory matching its capacity.
        Computes sequential IP addresses, registered MAC addresses, and unique Device IDs.
        """
        target_capacity = capacity or lab.default_capacity or 30
        lab.default_capacity = target_capacity

        existing_workstations = Workstation.query.filter_by(lab_id=lab.id).all()
        existing_seats = {ws.seat_number: ws for ws in existing_workstations}

        base_ip_str = lab.ip_start.strip() if lab.ip_start else None

        created_count = 0
        code_prefix = lab.code or f"LAB{lab.id}"

        for seat in range(1, target_capacity + 1):
            ws_ip = WorkstationService.generate_sequential_ip(base_ip_str, seat) if base_ip_str else None
            ws_mac = WorkstationService.generate_mac_address(lab.id, seat, lab.code)
            ws_dev_id = WorkstationService.generate_device_id(lab.code, seat)

            if seat in existing_seats:
                ws = existing_seats[seat]
                if not ws.mac_address:
                    ws.mac_address = ws_mac
                if not ws.device_id:
                    ws.device_id = ws_dev_id
                if ws_ip and not ws.ip_address:
                    ws.ip_address = ws_ip
            else:
                ws = Workstation(
                    lab_id=lab.id,
                    workstation_code=f"{code_prefix}-WS{seat:02d}",
                    seat_number=seat,
                    ip_address=ws_ip,
                    mac_address=ws_mac,
                    device_id=ws_dev_id,
                    secret_token=generate_workstation_token(),
                    status='active'
                )
                db.session.add(ws)
                created_count += 1

        # Automatically update lab.ip_end to the sequential IP of the last PC
        if base_ip_str:
            last_ip = WorkstationService.generate_sequential_ip(base_ip_str, target_capacity)
            if last_ip:
                lab.ip_end = last_ip

        db.session.commit()

        if admin_user_id and created_count > 0:
            AuditService.log(
                action="WORKSTATIONS_PROVISIONED",
                user_id=admin_user_id,
                target_type="Laboratory",
                target_id=lab.id,
                details=f"Provisioned {created_count} PCs with sequential IPs & MAC/Device IDs for {lab.name} (Capacity: {target_capacity})"
            )
        return created_count

    @staticmethod
    def find_workstation_for_request(lab_id: int, client_ip: str, token: str = None, device_id: str = None, mac_address: str = None):
        """
        Find a workstation in the given lab matching:
        1. Device ID if provided, OR
        2. Workstation token if provided, OR
        3. MAC address if provided, OR
        4. Exact registered IP match in this lab, OR
        5. Last octet seat match for local loopback testing.
        """
        # 1. Match by Device ID
        if device_id:
            ws = Workstation.query.filter_by(lab_id=lab_id, device_id=device_id, status='active').first()
            if ws:
                return ws

        # 2. Match by secret token
        if token:
            ws = Workstation.query.filter_by(lab_id=lab_id, secret_token=token, status='active').first()
            if ws:
                return ws

        # 3. Match by MAC address
        if mac_address:
            ws = Workstation.query.filter_by(lab_id=lab_id, mac_address=mac_address.strip().upper(), status='active').first()
            if ws:
                return ws

        # 4. Match by registered sequential IP
        if client_ip:
            ws = Workstation.query.filter_by(lab_id=lab_id, ip_address=client_ip, status='active').first()
            if ws:
                return ws

            # 5. Localhost / Loopback support
            try:
                last_octet = int(client_ip.split('.')[-1])
                ws = Workstation.query.filter_by(lab_id=lab_id, seat_number=last_octet, status='active').first()
                if ws:
                    return ws
            except (ValueError, IndexError):
                pass

        return None
