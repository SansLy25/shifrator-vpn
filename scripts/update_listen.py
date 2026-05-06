import json
with open('/tmp/server.json', 'r') as f:
    config = json.load(f)

for inbound in config.get('inbounds', []):
    if inbound.get('tag') == 'api':
        inbound['listen'] = '0.0.0.0'

with open('/tmp/server.json', 'w') as f:
    json.dump(config, f, indent=4)
