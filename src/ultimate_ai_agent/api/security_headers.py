from __future__ import annotations

from fastapi import Request, Response


SECURITY_HEADERS_POLICY_REF = "security-headers:p1-081:v1"

FASTAPI_SECURITY_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "base-uri 'none'; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "form-action 'self'; "
        "img-src 'self' data:; "
        "connect-src 'self' http://localhost:* http://127.0.0.1:* http://[::1]:*; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'"
    ),
    "Permissions-Policy": (
        "accelerometer=(), ambient-light-sensor=(), autoplay=(), camera=(), "
        "display-capture=(), encrypted-media=(), fullscreen=(), geolocation=(), "
        "gyroscope=(), magnetometer=(), microphone=(), midi=(), payment=(), "
        "picture-in-picture=(), publickey-credentials-get=(), screen-wake-lock=(), "
        "usb=(), web-share=(), xr-spatial-tracking=()"
    ),
}

HTTPS_ONLY_SECURITY_HEADERS: dict[str, str] = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}


def apply_fastapi_security_headers(request: Request, response: Response) -> Response:
    for name, value in FASTAPI_SECURITY_HEADERS.items():
        response.headers[name] = value
    if request.url.scheme == "https":
        for name, value in HTTPS_ONLY_SECURITY_HEADERS.items():
            response.headers[name] = value
    else:
        if "Strict-Transport-Security" in response.headers:
            del response.headers["Strict-Transport-Security"]
    response.headers["X-UAA-Security-Headers-Policy"] = SECURITY_HEADERS_POLICY_REF
    return response
