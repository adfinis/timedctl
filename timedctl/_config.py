import json
import os

CONFIG = {
    "username": "",
    "timed_url": "https://timed.example.com",
    "oidc_client_id": "timed",
    "oidc_auth_endpoint": "http://sso.example.com/auth/realms/test/protocol/openid-connect/auth",
    "oidc_token_endpoint": "http://sso.example.com/auth/realms/test/protocol/openid-connect/token",
}

# Get the path to the config file based on the $XDG_CONFIG_HOME environment variable
if not os.getenv("HOME"):
    raise EnvironmentError("$HOME is not set")

xdg_config_home = os.getenv(
    "XDG_CONFIG_HOME", os.path.join(os.getenv("HOME"), ".config")
)
config_dir = os.path.join(xdg_config_home, "timedctl")
config_file = os.path.join(config_dir, "config.json")

if not os.path.isfile(config_file):
    os.makedirs(config_dir, exist_ok=True)
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
