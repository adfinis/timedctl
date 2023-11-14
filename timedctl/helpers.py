"""
API unrelated helper functions.
"""
import json
import re
import sys
from datetime import timedelta
from os import getenv
from pathlib import Path

import click
import pyfzf
from rich import print
from tomlkit import dumps

DEFAULT_CONFIG = {
    "timed_url": "https://timed.example.com",
    "sso_url": "https://sso.example.com",
    "sso_realm": "example",
    "sso_client_id": "timedctl",
}


def msg(message, nonl=False):
    """Print a message in bold green."""
    print(f"[bold green]{message}[/bold green]", end="" if nonl else "\n")


def error_handler(error):
    """Handle errors."""
    print(f"[bold red]Error: {error}[/bold red]")
    sys.exit(1)


def fzf_wrapper(objects, title_key_array, prompt):
    """Wrap pyfzf."""
    # recursively resolve the title for each object
    # . is separator for the keys.
    titles = []
    for obj in objects:
        if isinstance(title_key_array[0], int):
            title = obj[title_key_array[0]]
        else:
            title = obj
            for key in title_key_array:
                title = title[key]
        titles.append(title)
    # run the fzf prompt
    result = [*pyfzf.FzfPrompt().prompt(titles, f"--prompt='{prompt}'"), None][0]
    # turn the results back into objects
    for obj in objects:
        if isinstance(title_key_array[0], int):
            title = obj[title_key_array[0]]
        else:
            title = obj
            for key in title_key_array:
                title = title[key]
        if title == result:
            return obj
    error_handler("ERR_FZF_EXCEPTION")
    return []


def time_picker(default=None):
    """Interactively pick a time using either arrow keys or typing."""
    res = ""
    while not re.match(r"^\d{1,2}:\d{2}:\d{2}$", res):
        print("[bold green]Duration[/bold green] (hh:mm:ss)", end="")
        res = click.prompt("", default=default)
    return res


def time_sum(arr):
    """Sum up an array of time strings."""
    total = timedelta()
    for line in arr[1:]:
        val = line[-1]
        total += val
    # format as HH:MM:SS
    return str(total)


def output_formatted(data, output_format):
    """Output data in a specified format."""
    match output_format:
        case "json":
            print(json.dumps(data, indent=4))
        case "csv":
            keys = data[0].keys()
            output = ",".join(keys) + "\n"
            for obj in data:
                output += ",".join(obj.values()) + "\n"
            print(output)
        case "text":
            for obj in data:
                for key, val in obj.items():
                    print(f"[{key}]: {val}, ", end="")
                print("")
        case _:
            print("Invalid format")


def get_config_file() -> Path:
    config_home = Path(getenv("XDG_CONFIG_HOME", "~/.config")).expanduser()
    config_file = config_home.joinpath("timedctl/config.toml")
    if config_file.exists():
        return config_file

    xdg_config_dirs = getenv("XDG_CONFIG_DIRS", "/etc/xdg/").split(":")
    for config_dir in xdg_config_dirs:
        system_wide_config = (
            Path(config_dir).expanduser().joinpath("timedctl/config.toml")
        )
        if system_wide_config.exists():
            return system_wide_config

    config_file.write_text(dumps(DEFAULT_CONFIG))
    print(f"[bold]Dumped default config file to {config_file.absolute()}[/bold]")
    return config_file
