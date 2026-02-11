"""
カスタム例外ハンドラー
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.security import APIError


async def api_exception_handler(request: Request, exc: APIError):
    """APIError用の例外ハンドラー"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


async def general_exception_handler(request: Request, exc: Exception):
    """一般的な例外ハンドラー"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"},
    )
