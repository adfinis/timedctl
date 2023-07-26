import rich
import re
import pyfzf
import click
import datetime
import sys
"""
API unrelated helper functions.
"""

def msg(message, nonl=False):
    """Print a message in bold green."""
    rich.print(f"[bold green]{message}[/bold green]", end="" if nonl else "\n")


def error_handler(error):
    """Handle errors."""
    rich.print(f"[bold red]Error: {error}[/bold red]")
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
        rich.print("[bold green]Duration[/bold green] (hh:mm:ss)", end="")
        res = click.prompt("", default=default)
    return res


def time_sum(arr):
    """Sum up an array of time strings."""
    total = datetime.timedelta()
    for line in arr[1:]:
        val = line[-1]
        total += val
    # format as HH:MM:SS
    return str(total)
