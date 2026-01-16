import base64
import time

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey


class KalshiTradingAuth:
    def __init__(self, api_key: str, private_key_pem: str):
        self.api_key = api_key
        self.private_key: RSAPrivateKey

        pem_content = private_key_pem.replace("\\n", "\n")

        try:
            loaded_key = serialization.load_pem_private_key(
                pem_content.encode(), password=None, backend=default_backend()
            )
            if not isinstance(loaded_key, RSAPrivateKey):
                raise ValueError("Private key must be an RSA key")
            self.private_key = loaded_key
        except Exception as e:
            raise ValueError(f"Failed to load RSA private key: {e}") from e

    def generate_signature(self, timestamp_ms: int, method: str, path: str) -> str:
        path_without_query = path.split("?")[0]
        message = f"{timestamp_ms}{method.upper()}{path_without_query}"

        signature = self.private_key.sign(
            message.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("utf-8")

    def get_auth_headers(self, method: str, path: str) -> dict[str, str]:
        timestamp_ms = int(time.time() * 1000)
        signature = self.generate_signature(timestamp_ms, method.upper(), path)

        return {
            "KALSHI-ACCESS-KEY": self.api_key,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": str(timestamp_ms),
        }
