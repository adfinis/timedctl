import os
import json

CONFIG = {
    "username": "",
    "oidc_client_id": "timed",
    "oidc_auth_endpoint": "http://sso.example.com/auth/realms/test/protocol/openid-connect/auth",
    "oidc_token_endpoint": "http://sso.example.com/auth/realms/test/protocol/openid-connect/token",
}


if not os.getenv("HOME"):
    raise Exception("HOME environment variable not set")
config_file = os.path.join(os.getenv("HOME", ""), ".config", "timedctl", "config.json")

if not os.path.isfile(config_file):
    os.makedirs(os.path.dirname(config_file), exist_ok=True)
    with open(config_file, "w") as f:
        json.dump(CONFIG, f)
    raise Exception(
        "Config file not found. Created a default one at {}. Please edit it in order for timedctl to work.".format(
            config_file
        )
    )
else:
    with open(config_file, "r") as f:
        user_config = json.load(f)
    for key in user_config:
        CONFIG[key] = user_config[key]
