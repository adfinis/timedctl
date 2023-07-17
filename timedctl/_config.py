#!/usr/bin/python3
"""Load and create a config file."""
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
    print("No config file found. Please enter the following infos.")
    for key in CONFIG:
        CONFIG[key] = input(f"{key}: ")
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(CONFIG, f)
else:
    with open(config_file, "r", encoding="utf-8") as f:
        user_config = json.load(f)
    for key in user_config:
        CONFIG[key] = user_config[key]
