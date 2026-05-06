import json

config = {
    "api": {
        "services": ["HandlerService"],
        "tag": "api"
    },
    "inbounds": [
        {
            "port": 4646,
            "protocol": "vless",
            "tag": "vless-reality",
            "settings": {
                "clients": [
                    {
                        "flow": "xtls-rprx-vision",
                        "id": "836129e0-50c4-4059-9d2c-e34b559eb45b"
                    },
                    {
                        "flow": "xtls-rprx-vision",
                        "id": "df780475-4546-4773-8a2c-cc158171fe83"
                    }
                ],
                "decryption": "none"
            },
            "streamSettings": {
                "network": "tcp",
                "realitySettings": {
                    "dest": "dl.google.com:443",
                    "privateKey": "-Nw7vnhQ-eiPlDXDvhv8JtVvYY1YZZEGTj5YZtQtfVg",
                    "serverNames": ["dl.google.com"],
                    "shortIds": ["daa9ad37f0f1ac27"]
                },
                "security": "reality"
            }
        },
        {
            "listen": "127.0.0.1",
            "port": 10085,
            "protocol": "dokodemo-door",
            "settings": {"address": "127.0.0.1"},
            "tag": "api"
        }
    ],
    "log": {"loglevel": "error"},
    "outbounds": [{"protocol": "freedom"}],
    "routing": {
        "rules": [
            {
                "inboundTag": ["api"],
                "outboundTag": "api",
                "type": "field"
            }
        ]
    }
}

print(json.dumps(config, indent=4))
