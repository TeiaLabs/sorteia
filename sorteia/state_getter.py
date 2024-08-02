from typing import Any, Callable

from fastapi import Request

from tauth.schemas.infostar import Infostar, InfostarExtra
from redbaby.pyobjectid import PyObjectId


def get(keyword: str) -> Callable[[Request], Any | None]:
    def wrapper(request: Request):
        if keyword in ["infostar", "creator"]:
            # Mock
            return Infostar(
                request_id=PyObjectId(),
                apikey_name="teialabs",
                authprovider_type="auth0",
                authprovider_org="teialabs",
                extra=InfostarExtra(
                    geolocation="",
                    jwt_sub="",
                    os="",
                    url="",
                    user_agent="",
                ),
                service_handle="allai--code",
                user_handle="teialabs@teialabs.com",
                user_owner_handle="teialabs",
                client_ip="",
            )

        try:
            return getattr(request.state, keyword)
        except AttributeError:
            return None

    return wrapper
