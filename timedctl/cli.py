#!/usr/bin/env python
"""CLI application for libtimed."""

import click
from click_aliases import ClickAliasedGroup

from timedctl.helpers import error_handler
from timedctl.timedctl import Timedctl

timed = Timedctl()


@click.group(cls=ClickAliasedGroup)
@click.option("--no-renew-token", default=False, is_flag=True)
@click.option("--config", "custom_config", default=None, type=str)
@click.version_option(package_name="timedctl")
def timedctl(no_renew_token, custom_config):
    """Use timedctl."""
    timed.load_config(custom_config)
    timed.setup(no_renew_token)


@timedctl.command("force-renew")
def force_renew():
    """Force renew token."""
    timed.force_renew()


@timedctl.group(cls=ClickAliasedGroup, aliases=["g", "show", "describe"])
def get():
    """Get different things."""


@get.group(cls=ClickAliasedGroup)
def data():
    """Get raw data for building custom scripts."""


@data.command("customers")
@click.option(
    "--format",
    "output_format",
    default="json",
    type=click.Choice(["json", "csv", "text"]),
)
def get_customers(**kwargs):
    """Get customers."""
    timed.get_customers(**kwargs)


@data.command("projects")
@click.option(
    "--format",
    "output_format",
    default="json",
    type=click.Choice(["json", "csv", "text"]),
)
@click.option("--customer-id", default=None, type=int)
@click.option("--customer-name", default=None, type=str)
@click.option("--archived", default=False, is_flag=True)
def get_projects(**kwargs):
    """Get projects."""
    timed.get_projects(**kwargs)


@data.command("tasks")
@click.option(
    "--format",
    "output_format",
    default="json",
    type=click.Choice(["json", "csv", "text"]),
)
@click.option("--customer-id", default=None, type=int)
@click.option("--customer-name", default=None, type=str)
@click.option("--project-id", default=None, type=int)
@click.option("--project-name", default=None, type=str)
@click.option("--archived", default=False, is_flag=True)
def get_tasks(
    **kwargs,
):
    """Get tasks."""
    timed.get_tasks(**kwargs)


@get.command("overtime", aliases=["t", "ot", "undertime"])
@click.option("--date", default=None)
def get_overtime(**kwargs):
    """Get overtime of user."""
    timed.get_overtime(**kwargs)


@get.command("reports", aliases=["report", "r"])
@click.option("--date", default=None)
def get_reports(**kwargs):
    """Get reports."""
    timed.get_reports(**kwargs)


@get.command("activities", aliases=["a", "ac", "activity"])
@click.option("--date", default=None)
def get_activities(**kwargs):
    """Get activities."""
    timed.get_activities(**kwargs)


@get.command("absences", aliases=["abs"])
def get_absences():
    """Get absences."""
    error_handler("ERR_NOT_IMPLEMENTED")


@timedctl.group(cls=ClickAliasedGroup, aliases=["rm", "d", "remove", "del"])
def delete():
    """Delete different things."""


@delete.command("report", aliases=["r"])
@click.option("--date", default=None)
def delete_report(**kwargs):
    """Delete report(s)."""
    timed.delete_report(**kwargs)


@delete.command("holiday", aliases=["h"])
def delete_holiday():
    """Delete holiday(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@delete.command("absence", aliases=["abs"])
def delete_absence():
    """Delete absence(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@timedctl.group(cls=ClickAliasedGroup, aliases=["a", "create"])
def add():
    """Add different things."""


@add.command("report", aliases=["r"])
@click.option("--customer", default=None)
@click.option("--project", default=None)
@click.option("--task", default=None)
@click.option("--description", default=None)
@click.option("--duration", default=None)
@click.option("--show-archived", default=False, is_flag=True)
def add_report(**kwargs):
    """Add report(s)."""
    timed.add_report(**kwargs)


@add.command("holiday", aliases=["h"])
def add_holiday():
    """Add holiday(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@add.command("absence", aliases=["abs"])
def add_absence():
    """Add absence(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@timedctl.group(cls=ClickAliasedGroup, aliases=["e", "edit", "update"])
def edit():
    """Edit different things."""


@edit.command("report", aliases=["r"])
@click.option("--date", default=None)
def edit_report(**kwargs):
    """Edit report(s)."""
    timed.edit_report(**kwargs)


@edit.command("holiday", aliases=["h"])
def edit_holiday():
    """Edit holiday(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@edit.command("absence", aliases=["abs"])
def edit_absence():
    """Edit absence(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@timedctl.group(cls=ClickAliasedGroup, aliases=["ac"])
def activity():
    """Do stuff with activities."""


@activity.command("start", aliases=["add", "a"])
@click.argument("comment")
@click.option("--customer", default=None)
@click.option("--project", default=None)
@click.option("--task", default=None)
@click.option("--show-archived", default=False, is_flag=True)
@click.option("--start-time", "start", default=None)
def start_activity(**kwargs):
    """Start recording activity."""
    timed.start_activity(**kwargs)


@activity.command("stop", aliases=["end", "finish"])
def stop_activity(**kwargs):
    """Stop current activity."""
    timed.stop_activity(**kwargs)


@activity.command("show", aliases=["s", "get", "info"])
@click.option("--short", default=False, is_flag=True)
def show_activity(**kwargs):
    """Show current activity."""
    timed.show_activity(**kwargs)


@activity.command("restart", aliases=["r", "continue", "resume"])
@click.option("--date", default=None)
def restart_activity(**kwargs):
    """Restart an activity."""
    timed.restart_activity(**kwargs)


@activity.command("delete", aliases=["d", "rm", "remove"])
@click.option("--date", default=None)
def delete_activity(**kwargs):
    """Delete an activity."""
    timed.delete_activity(**kwargs)


@activity.command("generate-timesheet", aliases=["gts", "ts"])
def activity_generate_timesheet(**kwargs):
    """Generate the timesheet of the current activities."""
    timed.activity_generate_timesheet(**kwargs)


if __name__ == "__main__":
    timedctl()
