import json
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class ResponseEnvelopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}:
            return await call_next(request)

        response = await call_next(request)

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        if not body:
            return response

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=response.status_code,
                content={"success": True, "data": body.decode("utf-8", errors="ignore"), "message": "OK", "error": None},
            )

        if isinstance(payload, dict) and {"success", "data", "message", "error"}.issubset(payload.keys()):
            wrapped_payload = payload
        else:
            wrapped_payload = {
                "success": 200 <= response.status_code < 400,
                "data": payload if response.status_code < 400 else None,
                "message": "OK" if response.status_code < 400 else "Request failed",
                "error": None if response.status_code < 400 else payload,
            }

        wrapped = JSONResponse(status_code=response.status_code, content=wrapped_payload)
        for key, value in response.headers.items():
            if key.lower() not in {"content-length", "content-type"}:
                wrapped.headers[key] = value
        return wrapped
