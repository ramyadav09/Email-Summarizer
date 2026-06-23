from fastapi import Header, HTTPException


def get_token(authorization: str = Header(...)) -> str:
    """Extract and validate the Bearer token from the Authorization header.

    Usage in routers:
        @router.get("/endpoint")
        def my_endpoint(token: str = Depends(get_token)):
            ...
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing access token")

    return token
