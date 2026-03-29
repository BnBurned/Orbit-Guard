from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class LocalOnlyMiddleware(BaseHTTPMiddleware):
    """IP erişim kontrolü: yalnızca 127.0.0.1 ve ::1 adreslerine izin verir."""

    ALLOWED_HOSTS = {"127.0.0.1", "::1"}

    async def dispatch(self, request: Request, call_next):
        client_host = request.client.host if request.client else None
        if client_host not in self.ALLOWED_HOSTS:
            return JSONResponse({"detail": "Forbidden"}, status_code=403)
        return await call_next(request)
