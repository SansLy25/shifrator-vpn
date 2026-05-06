import urllib.parse
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VpnLinkBuilder:
    host: str
    port: int
    public_key: str
    short_id: str
    sni: str
    flow: str = "xtls-rprx-vision"

    def build(self, uuid: str, name: str) -> str:
        params = {
            "type": "tcp",
            "security": "reality",
            "pbk": self.public_key,
            "fp": "chrome",
            "sni": self.sni,
            "sid": self.short_id,
            "flow": self.flow,
        }
        query_string = urllib.parse.urlencode(params)
        fragment = urllib.parse.quote(name)
        return f"vless://{uuid}@{self.host}:{self.port}?{query_string}#{fragment}"
