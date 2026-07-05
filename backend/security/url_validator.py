import socket
import structlog
from urllib.parse import urlparse, urlunparse
from fastapi import HTTPException

logger = structlog.get_logger("url_validator")

# Disallowed internal/private IP ranges for SSRF protection
# 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 127.0.0.0/8, 169.254.0.0/16 (AWS metadata)
def is_internal_ip(ip_str: str) -> bool:
    try:
        import ipaddress
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False

def validate_and_normalize_url(url: str) -> str:
    """
    Validates a given URL for SSRF protection and normalizes it.
    Throws HTTPException if the URL is unsafe.
    """
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"https://{url}"

    try:
        parsed = urlparse(url)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid URL format.")

    if parsed.scheme not in ["http", "https"]:
        raise HTTPException(status_code=400, detail="Only HTTP and HTTPS protocols are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="Invalid domain name.")

    # 1. Block explicitly localhost or internal domains
    if hostname in ["localhost", "127.0.0.1", "::1"] or hostname.endswith(".internal"):
        logger.warning("ssrf_attempt_blocked_domain", url=url, hostname=hostname)
        raise HTTPException(status_code=400, detail="Internal domains are not allowed.")

    # 2. Resolve IP to block DNS rebinding/SSRF
    try:
        # resolve hostname to IP
        ip_addr = socket.gethostbyname(hostname)
        if is_internal_ip(ip_addr):
            logger.warning("ssrf_attempt_blocked_ip", url=url, hostname=hostname, resolved_ip=ip_addr)
            raise HTTPException(status_code=400, detail="Target resolves to an internal network address.")
    except socket.gaierror:
        # If it doesn't resolve, it's either an invalid domain or potentially safe to let httpx handle the error later
        # We'll allow it to pass but httpx will likely fail.
        pass

    # Normalize URL (remove trailing slash)
    normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip('/'), parsed.params, parsed.query, parsed.fragment))
    return normalized
