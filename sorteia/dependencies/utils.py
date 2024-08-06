from tauth.schemas import Infostar


def authprovider_parser_for_infostar(infostar: Infostar) -> str:
    org: str = infostar.authprovider_org
    if org == "/":
        user_email: str = infostar.user_handle
        return user_email.split("@")[-1].split(".", 1)[0]
    return org.strip("/")
