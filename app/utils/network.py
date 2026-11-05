import ipaddress
import logging
from flask import request, current_app

logger = logging.getLogger(__name__)


def get_real_client_ip() -> str:
    """
    Safely extract the client IP address.
    If behind a trusted reverse proxy (configured via BEHIND_PROXY),
    parses X-Forwarded-For properly. Otherwise, uses request.remote_addr.
    """
    behind_proxy = current_app.config.get('BEHIND_PROXY', False)
    
    if behind_proxy:
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            # First IP in the list is the original client
            parts = [ip.strip() for ip in forwarded_for.split(',')]
            if parts:
                return parts[0]
                
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip.strip()
            
    return request.remote_addr or '127.0.0.1'


def is_ip_in_range(ip_str: str, range_start: str, range_end: str) -> bool:
    """
    Check if an IP string falls within the range [range_start, range_end].
    Supports IPv4.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        start = ipaddress.ip_address(range_start)
        end = ipaddress.ip_address(range_end)
        return start <= ip <= end
    except ValueError:
        return False


def is_ip_in_subnet(ip_str: str, cidr_or_subnet: str) -> bool:
    """Check if an IP string belongs to a CIDR network (e.g. 192.168.1.0/24)."""
    try:
        ip = ipaddress.ip_address(ip_str)
        net = ipaddress.ip_network(cidr_or_subnet, strict=False)
        return ip in net
    except ValueError:
        return False


def extract_pc_number_from_ip(ip_str: str) -> int:
    """
    Extract the host part or fallback integer from an IP address.
    Returns 0 if non-parsable.
    """
    try:
        parts = ip_str.split('.')
        if len(parts) == 4:
            return int(parts[-1])
    except Exception:
        pass
    return 0

