import os
import json

CONFIG = {
        "username": "",
}


if not os.getenv('HOME'):
    raise Exception("HOME environment variable not set")
config_file = os.path.join(os.getenv('HOME', ""), '.config', 'timedctl', 'config.ini')

if not os.path.isfile(config_file):
    pass
else:
    with open(config_file, 'r') as f:
        user_config = json.load(f)
    for key in CONFIG:
        if key not in CONFIG:
            CONFIG[key] = user_config[key]

