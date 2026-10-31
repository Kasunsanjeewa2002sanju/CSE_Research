import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple

BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("10.0.0.0/8"),        # Private network
    ipaddress.ip_network("172.16.0.0/12"),     # Private network
    ipaddress.ip_network("192.168.0.0/16"),    # Private network
    ipaddress.ip_network("169.254.0.0/16"),    # Link-local / AWS metadata (169.254.169.254)
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),          # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),         # IPv6 link-local
    ipaddress.ip_network("0.0.0.0/8"),         # Broadcast / current network
]

BLOCKED_HOSTNAMES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "metadata.google.internal",
    "instance-data",
}

def validate_url_safety(url: str) -> Tuple[bool, str]:
    """
    Validate that a given URL is safe to fetch and not attempting SSRF attacks
    against internal networks, loopback addresses, or cloud metadata endpoints.
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty."
        
    url = url.strip()
    if len(url) > 2048:
        return False, "URL length exceeds allowable limit."
        
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Malformed URL format."
        
    if parsed.scheme not in ("http", "https"):
        return False, f"Unsupported scheme: '{parsed.scheme}'. Only http and https are permitted."
        
    hostname = parsed.hostname
    if not hostname:
        return False, "URL does not contain a valid hostname."
        
    hostname_lower = hostname.lower()
    if hostname_lower in BLOCKED_HOSTNAMES or hostname_lower.endswith(".local") or hostname_lower.endswith(".internal"):
        return False, f"Access to host '{hostname}' is restricted by security policy."
        
    # Resolve hostname to IP to prevent DNS rebinding or numeric IP bypass
    try:
        # Get all resolved addresses
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
        for item in addr_info:
            ip_str = item[4][0]
            ip_obj = ipaddress.ip_address(ip_str)
            for blocked_net in BLOCKED_IP_NETWORKS:
                if ip_obj in blocked_net:
                    return False, f"Resolved IP address '{ip_str}' is within a forbidden or private address range."
    except socket.gaierror:
        return False, f"Failed to resolve hostname: '{hostname}'."
    except Exception as e:
        return False, f"Security check error: {str(e)}"
        
    return True, "URL is valid and safe."

def sanitize_text(text: str, max_length: int = 5000) -> str:
    """Sanitize user-provided text inputs, stripping null bytes and limiting length."""
    if not text:
        return ""
    # Strip null bytes and non-printable control characters except standard whitespace
    cleaned = "".join(ch for ch in text if ch.isprintable() or ch in "\r\n\t")
    return cleaned.strip()[:max_length]
