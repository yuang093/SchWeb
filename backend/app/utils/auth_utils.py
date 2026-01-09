import base64

def get_basic_auth_header(client_id: str, client_secret: str) -> str:
    """
    產生 Schwab 要求的 Basic Base64(Key:Secret) 憑證
    """
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded_credentials}"
