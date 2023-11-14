#!/usr/bin/env python
"""CLI application for libtimed."""

import click
from click_aliases import ClickAliasedGroup

from timedctl.helpers import error_handler, get_config_file
from timedctl.timedctl import Timedctl


@click.group(cls=ClickAliasedGroup)
@click.option("--no-renew-token", default=False, is_flag=True)
@click.option(
    "--config",
    default=get_config_file(),
    type=click.Path(exists=True, dir_okay=False),
    help="The configuration to read from",
)
@click.version_option(package_name="timedctl")
@click.pass_context
def timedctl(ctx, no_renew_token, config):
    """Use timedctl."""
    ctx.obj = Timedctl(config_file=config, no_renew_token=no_renew_token)


@timedctl.command("force-renew")
@click.pass_obj
def force_renew(timed):
    """Force renew token."""
    timed.force_renew()


@timedctl.group(cls=ClickAliasedGroup, aliases=["g", "show", "describe"])
@click.pass_context
def get(ctx):
    """Get different things."""


@get.group(cls=ClickAliasedGroup)
@click.pass_context
def data(ctx):
    """Get raw data for building custom scripts."""


@data.command("customers")
@click.option(
    "--format",
    "output_format",
    default="json",
    type=click.Choice(["json", "csv", "text"]),
)
@click.pass_obj
def get_customers(timed, **kwargs):
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
@click.pass_obj
def get_projects(timed, **kwargs):
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
@click.pass_obj
def get_tasks(
    timed,
    **kwargs,
):
    """Get tasks."""
    timed.get_tasks(**kwargs)


@get.command("overtime", aliases=["t", "ot", "undertime"])
@click.option("--date", default=None)
@click.pass_obj
def get_overtime(timed, **kwargs):
    """Get overtime of user."""
    timed.get_overtime(**kwargs)


@get.command("reports", aliases=["report", "r"])
@click.option("--date", default=None)
@click.pass_obj
def get_reports(timed, **kwargs):
    """Get reports."""
    timed.get_reports(**kwargs)


@get.command("activities", aliases=["a", "ac", "activity"])
@click.option("--date", default=None)
@click.pass_obj
def get_activities(timed, **kwargs):
    """Get activities."""
    timed.get_activities(**kwargs)


@get.command("absences", aliases=["abs"])
@click.pass_obj
def get_absences(timed):
    """Get absences."""
    error_handler("ERR_NOT_IMPLEMENTED")


@timedctl.group(cls=ClickAliasedGroup, aliases=["rm", "d", "remove", "del"])
@click.pass_context
def delete(ctx):
    """Delete different things."""


@delete.command("report", aliases=["r"])
@click.option("--date", default=None)
@click.pass_obj
def delete_report(timed, **kwargs):
    """Delete report(s)."""
    timed.delete_report(**kwargs)


@delete.command("holiday", aliases=["h"])
@click.pass_obj
def delete_holiday(timed):
    """Delete holiday(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@delete.command("absence", aliases=["abs"])
@click.pass_obj
def delete_absence(timed):
    """Delete absence(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@timedctl.group(cls=ClickAliasedGroup, aliases=["a", "create"])
@click.pass_context
def add(ctx):
    """Add different things."""


@add.command("report", aliases=["r"])
@click.option("--customer", default=None)
@click.option("--project", default=None)
@click.option("--task", default=None)
@click.option("--description", default=None)
@click.option("--duration", default=None)
@click.option("--show-archived", default=False, is_flag=True)
@click.pass_obj
def add_report(timed, **kwargs):
    """Add report(s)."""
    timed.add_report(**kwargs)


@add.command("holiday", aliases=["h"])
@click.pass_obj
def add_holiday(timed):
    """Add holiday(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@add.command("absence", aliases=["abs"])
@click.pass_obj
def add_absence(timed):
    """Add absence(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@timedctl.group(cls=ClickAliasedGroup, aliases=["e", "edit", "update"])
@click.pass_context
def edit(ctx):
    """Edit different things."""


@edit.command("report", aliases=["r"])
@click.option("--date", default=None)
@click.pass_obj
def edit_report(timed, **kwargs):
    """Edit report(s)."""
    timed.edit_report(**kwargs)


@edit.command("holiday", aliases=["h"])
@click.pass_obj
def edit_holiday(timed):
    """Edit holiday(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@edit.command("absence", aliases=["abs"])
@click.pass_obj
def edit_absence(timed):
    """Edit absence(s)."""
    error_handler("ERR_NOT_IMPLEMENTED")


@timedctl.group(cls=ClickAliasedGroup, aliases=["ac"])
@click.pass_context
def activity(ctx):
    """Do stuff with activities."""


@activity.command("start", aliases=["add", "a"])
@click.argument("comment")
@click.option("--customer", default=None)
@click.option("--project", default=None)
@click.option("--task", default=None)
@click.option("--show-archived", default=False, is_flag=True)
@click.option("--start-time", "start", default=None)
@click.pass_obj
def start_activity(timed, **kwargs):
    """Start recording activity."""
    timed.start_activity(**kwargs)


@activity.command("stop", aliases=["end", "finish"])
@click.pass_obj
def stop_activity(timed, **kwargs):
    """Stop current activity."""
    timed.stop_activity(**kwargs)


@activity.command("show", aliases=["s", "get", "info"])
@click.option("--short", default=False, is_flag=True)
@click.pass_obj
def show_activity(timed, **kwargs):
    """Show current activity."""
    timed.show_activity(**kwargs)


@activity.command("restart", aliases=["r", "continue", "resume"])
@click.option("--date", default=None)
@click.pass_obj
def restart_activity(timed, **kwargs):
    """Restart an activity."""
    timed.restart_activity(**kwargs)


@activity.command("delete", aliases=["d", "rm", "remove"])
@click.option("--date", default=None)
@click.pass_obj
def delete_activity(timed, **kwargs):
    """Delete an activity."""
    timed.delete_activity(**kwargs)


@activity.command("generate-timesheet", aliases=["gts", "ts"])
@click.pass_obj
def activity_generate_timesheet(timed, **kwargs):
    """Generate the timesheet of the current activities."""
    timed.activity_generate_timesheet(**kwargs)


if __name__ == "__main__":
    timedctl()
