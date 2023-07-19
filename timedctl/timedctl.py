#!/usr/bin/env python
"""CLI application for libtimed."""

import datetime
import tomllib
import os
import re
import sys

import click
import pyfzf
import rich
import terminaltables
from tomlkit import dump
from libtimed import TimedAPIClient
from libtimed.oidc import OIDCClient


def load_config():
    """Load the timedctl config."""
    cfg = {
        "username": "test",
        "timed_url": "https://timed.example.com",
        "sso_url": "https://sso.example.com",
        "sso_realm": "example",
        "sso_client_id": "timedctl",
    }

    # Get the path to the config file based on the $XDG_config_HOME environment variable
    if not os.getenv("HOME"):
        raise EnvironmentError("$HOME is not set")

    xdg_config_home = os.getenv(
        "XDG_CONFIG_HOME", os.path.join(os.getenv("HOME"), ".config")
    )
    config_dir = os.path.join(xdg_config_home, "timedctl")
    config_file = os.path.join(config_dir, "config.toml")

    if not os.path.isfile(config_file):
        os.makedirs(config_dir, exist_ok=True)
        print("No config file found. Please enter the following infos.")
        for key in cfg:
            cfg[key] = input(f"{key} ({cfg[key]}): ")
        with open(config_file, "w", encoding="utf-8") as file:
            dump(cfg, file)
    else:
        with open(config_file, "rb") as file:
            user_config = tomllib.load(file)
        for key in user_config:
            cfg[key] = user_config[key]
    return cfg


config = load_config()


def client_setup():
    """Set up the timed client."""
    # initialize libtimed
    url = config.get("timed_url")
    api_namespace = "api/v1"

    # Auth stuff
    client_id = config.get("sso_client_id")
    sso_url = config.get("sso_url")
    sso_realm = config.get("sso_realm")
    auth_path = "timedctl/auth"
    oidc_client = OIDCClient(client_id, sso_url, sso_realm, auth_path)
    token = oidc_client.authorize()
    return TimedAPIClient(token, url, api_namespace)


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
    while not re.match(r"^\d{2}:\d{2}:\d{2}$", res):
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


def select_report(date):
    """FZF prompt to select a report."""
    reports = timed.reports.get(
        {"date": date}, include="task,task.project,task.project.customer"
    )
    report_view = []
    for report in reports:
        task = report["relationships"]["task"]
        report_view.append(
            [
                task["attributes"]["name"],
                report["attributes"]["comment"],
                str(report["attributes"]["duration"]),
                task["id"],
                report["id"],
            ]
        )
    # get longest key per value
    max_key_lengths = [max(map(len, col)) for col in zip(*report_view)]
    # pad all the values
    report_view = [
        [
            report_view[i][j].ljust(max_key_lengths[j])
            for j in range(len(report_view[i]))
        ]
        for i in range(len(report_view))
    ]
    # create a list for fzf
    fzf_obj = []
    for row in report_view:
        fzf_obj.append(
            [" | ".join([row[0], row[1], row[2]]), row[1], row[2], row[3], row[4]]
        )

    report = fzf_wrapper(fzf_obj, [0], "Select a report: ")
    return report


timed = client_setup()


@click.group()
def timedctl():
    """Use timedctl."""
    pass  # pylint: disable=W0107


@timedctl.group()
def get():
    """Get different things."""
    pass  # pylint: disable=W0107


@get.command("overtime")
@click.option("--date", default=None)
def get_overtime(date):
    """Get overtime of user."""
    user = timed.users.me["id"]
    overtime = timed.overtime.get({"user": user, "date": date})
    msg(f"Currrent overtime is: {overtime}")


@get.command("reports")
@click.option("--date", default=None)
def get_reports(date):
    """Get reports."""
    reports = timed.reports.get(
        {"date": date}, include="task,task.project,task.project.customer"
    )
    table = [["Customer", "Project", "Task", "Comment", "Duration"]]
    for report in reports:
        task_obj = report["relationships"]["task"]
        task = task_obj["attributes"]["name"]

        project_obj = timed.projects.get(id=task_obj["relationships"]["project"]["id"])
        project = project_obj["attributes"]["name"]

        customer_obj = timed.customers.get(
            id=project_obj["relationships"]["customer"]["data"]["id"]
        )
        customer = customer_obj["attributes"]["name"]

        table.append(
            [
                customer,
                project,
                task,
                report["attributes"]["comment"],
                report["attributes"]["duration"],
            ]
        )
    output = terminaltables.SingleTable(table)
    msg(f"Reports for {date if date is not None else 'today'}:")
    click.echo(output.table)
    msg(f"Total: {time_sum(table)}")


@get.command("activities")
@click.option("--date", default=None)
def get_activities(date):
    """Get activities."""
    activities = timed.activities.get(
        {"day": date}, include="task,task.project,task.project.customer"
    )
    table = [["Activity", "Comment", "Start", "End"]]
    for activity in activities:
        task_obj = activity["relationships"]["task"]
        task = task_obj["attributes"]["name"]

        project_obj = timed.projects.get(id=task_obj["relationships"]["project"]["id"])
        project = project_obj["attributes"]["name"]

        customer_obj = timed.customers.get(
            id=project_obj["relationships"]["customer"]["data"]["id"]
        )
        customer = customer_obj["attributes"]["name"]

        table.append(
            [
                f"{customer} > {project} > {task}",
                activity["attributes"]["comment"],
                activity["attributes"]["from-time"].strftime("%H:%M:%S"),
                activity["attributes"]["to-time"].strftime("%H:%M:%S")
                if activity["attributes"]["to-time"] is not None
                else "active",
            ]
        )
    output = terminaltables.SingleTable(table)
    msg(f"Activities for {date if date is not None else 'today'}:")
    click.echo(output.table)


@get.command("absences")
def get_absences():
    """Get absences."""


@timedctl.group()
def delete():
    """Delete different things."""
    pass  # pylint: disable=W0107


@delete.command("report")
@click.option("--date", default=None)
def delete_report(date):
    """Delete report(s)."""
    report = select_report(date)
    res = pyfzf.FzfPrompt().prompt(
        ["Yes", "No"], f"--prompt 'Are you sure? Delete \"{report[1]}\"?'"
    )
    if res[0] == "Yes":
        req = timed.reports.delete(report[-1])
        if req.status_code == 204:
            msg(f'Deleted report "{report[1]}"')
        else:
            error_handler("ERR_DELETION_FAILED")
    else:
        error_handler("ERR_DELETION_ABORTED")


@delete.command("holiday")
def delete_holiday():
    """Delete holiday(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@delete.command("absence")
def delete_absence():
    """Delete absence(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@timedctl.group()
def add():
    """Add different things."""
    pass  # pylint: disable=W0107


@add.command("report")
def add_report():
    """Add report(s)."""
    customers = timed.customers.get()
    # ask the user to select a customer
    msg("Select a customer")
    # select a customer
    customer = fzf_wrapper(customers, ["attributes", "name"], "Select a customer: ")
    # get projects
    projects = timed.projects.get({"customer": customer["id"]})
    # select a project
    project = fzf_wrapper(projects, ["attributes", "name"], "Select a project: ")
    # get tasks
    tasks = timed.tasks.get({"project": project["id"]})
    # select a task
    task = fzf_wrapper(tasks, ["attributes", "name"], "Select a task: ")
    # ask the user to enter a description
    msg("Enter a description")
    # get description
    description = click.prompt("")
    # ask the user to enter a duration
    duration = time_picker()
    # create the report
    res = timed.reports.post(
        {"duration": duration, "comment": description},
        {
            "task": task["id"],
        },
    )
    if res.status_code == 201:
        msg("Report created successfully")
        return
    # handle exception
    error_handler("ERR_REPORT_CREATION_FAILED")


@add.command("holiday")
def add_holiday():
    """Add holiday(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@add.command("absence")
def add_absence():
    """Add absence(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@timedctl.group()
def edit():
    """Edit different things."""
    pass  # pylint: disable=W0107


@edit.command("report")
@click.option("--date", default=None)
def edit_report(date):
    """Edit report(s)."""
    report = select_report(date)

    msg("Comment", True)
    comment = click.prompt("", default=report[1].strip())
    duration = time_picker(default=report[2])
    res = pyfzf.FzfPrompt().prompt(["No", "Yes"], "--prompt 'Are you sure?'")
    if res == ["Yes"]:
        res = timed.reports.patch(
            report[-1], {"comment": comment, "duration": duration}, {"task": report[-2]}
        )
        if res.status_code == 200:
            msg("Report updated successfully")
            return
        # handle exception
        error_handler("ERR_REPORT_UPDATE_FAILED")
    else:
        error_handler("ERR_REPORT_UPDATE_ABORTED")


@edit.command("holiday")
def edit_holiday():
    """Edit holiday(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@edit.command("absence")
def edit_absence():
    """Edit absence(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@timedctl.group()
def activity():
    """Do stuff with activities."""
    pass  # pylint: disable=W0107


@activity.command()
@click.argument("comment")
def start(comment):
    """Start recording activity."""
    customers = timed.customers.get()
    # ask the user to select a customer
    msg("Select a customer")
    # select a customer
    customer = fzf_wrapper(customers, ["attributes", "name"], "Select a customer: ")
    # get projects
    projects = timed.projects.get({"customer": customer["id"]})
    # select a project
    project = fzf_wrapper(projects, ["attributes", "name"], "Select a project: ")
    # get tasks
    tasks = timed.tasks.get({"project": project["id"]})
    # select a task
    task = fzf_wrapper(tasks, ["attributes", "name"], "Select a task: ")
    # create the activity
    res = timed.activities.start(
        attributes={"comment": comment}, relationships={"task": task["id"]}
    )

    if res.status_code == 201:
        msg(f"Activity {comment} started successfully.")
        return
    # handle exception
    error_handler("ERR_ACTIVITY_START_FAILED")


@activity.command()
def stop():
    """Stop current activity."""
    msg("Activity stopped successfully.")


@activity.command()
def show():
    """Show current activity."""
    current_activity = timed.activities.current
    if current_activity:
        msg(
            f"Current activity: {current_activity['attributes']['comment']} (Since {current_activity['attributes']['from-time'].strftime('%H:%M:%S')})"
        )
    else:
        error_handler("ERR_NO_CURRENT_ACTIVITY")


@activity.command()
def generate_timesheet():
    """Generate the timesheet of the current activities."""
    activities = timed.activities.get()
    if activities:
        for activity in activities:
            if not activity["attributes"]["transferred"]:
                from_time = activity["attributes"]["from-time"]
                to_time = activity["attributes"]["to-time"]
                duration = to_time - from_time
                task = activity["relationships"]["task"]["data"]["id"]
                timed.reports.post(
                    {
                        "duration": duration,
                        "comment": activity["attributes"]["comment"],
                    },
                    {"task": task},
                )
                timed.activities.patch(
                    activity["id"], {"transferred": True}, {"task": task}
                )
        msg("Timesheet generated successfully.")
    else:
        error_handler("ERR_NO_ACTIVITIES")


if __name__ == "__main__":
    load_config()
    timedctl()
