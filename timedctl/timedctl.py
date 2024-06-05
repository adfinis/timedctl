#!/usr/bin/env python
"""CLI application for libtimed."""

import os
import re
import time
import webbrowser
from datetime import datetime, timedelta

import click
import jwt
import keyring
import pyfzf
import requests
import tomllib
from libtimed import TimedAPIClient
from rich import print
from rich.table import Table
from tomlkit import dump

from timedctl.helpers import (
    error_handler,
    fzf_wrapper,
    msg,
    output_formatted,
    time_picker,
)

TIMEOUT = 30


class Timedctl:
    def __init__(self):
        pass

    def load_config(self, custom_config=None):
        """Load the timedctl config."""
        cfg = {
            "username": "test",
            "timed_url": "https://timed.example.com",
            "sso_discovery_url": "https://sso.example.com/realms/example",
            "sso_client_id": "timedctl",
        }

        # Get the path to the config file based on the
        # $XDG_config_HOME environment variable
        if not os.getenv("HOME"):
            raise OSError("$HOME is not set")

        xdg_config_home = os.getenv(
            "XDG_CONFIG_HOME",
            os.path.join(os.getenv("HOME"), ".config"),
        )
        config_dir = os.path.join(xdg_config_home, "timedctl")
        if custom_config:
            config_file = custom_config
        else:
            config_file = os.path.join(config_dir, "config.toml")

        if not os.path.isfile(config_file):
            os.makedirs(config_dir, exist_ok=True)
            click.echo("No config file found. Please enter the following infos.")
            for key in cfg:
                cfg[key] = input(f"{key} ({cfg[key]}): ")
            with open(config_file, "w", encoding="utf-8") as file:
                dump(cfg, file)
        else:
            with open(config_file, "rb") as file:
                user_config = tomllib.load(file)

            # Migration from sso_url & sso_realm to sso_discovery_url
            if (
                "sso_discovery_url" not in user_config
                and "sso_url" in user_config
                and "sso_realm" in user_config
            ):
                user_config["sso_discovery_url"] = (
                    user_config["sso_url"] + "/realms/" + user_config["sso_realm"]
                )
                del user_config["sso_url"]
                del user_config["sso_realm"]

                with open(config_file, "w", encoding="utf-8") as file:
                    dump(user_config, file)

            for key in user_config:
                cfg[key] = user_config[key]
        self.config = cfg

    def setup(self, no_renew_token=False):
        """Set up the timed client."""
        # initialize libtimed
        url = self.config.get("timed_url")
        api_namespace = "api/v1"
        client_id = self.config["sso_client_id"]

        access_token = keyring.get_password(
            "system", "timedctl_token_" + client_id + "_access"
        )
        decode_options = {"verify_signature": False, "verify_exp": "verify_signature"}
        try:
            # Check if access_token is valid
            jwt.decode(access_token, leeway=-30, options=decode_options)

        except (jwt.exceptions.ExpiredSignatureError, jwt.exceptions.DecodeError):
            # Access token expired or missing
            refresh_token = keyring.get_password(
                "system", "timedctl_token_" + client_id + "_refresh"
            )
            try:
                jwt.decode(refresh_token, leeway=-10, options=decode_options)
                access_token = self.refresh_token(refresh_token)

            except (jwt.exceptions.ExpiredSignatureError, jwt.exceptions.DecodeError):
                # Refresh token expired or missing
                if no_renew_token:
                    error_handler("ERR_TOKEN_MISSING_OR_EXPIRED")

                access_token = self.login()

        self.timed = TimedAPIClient(access_token, url, api_namespace)

    def get_openid_configuration(self):
        """Return the OpenID configuration."""
        sso_discovery_url = self.config.get("sso_discovery_url")

        # Retrieve OpenID configuration
        openid_configuration = requests.get(
            f"{sso_discovery_url}/.well-known/openid-configuration", timeout=TIMEOUT
        ).json()
        if "error" in openid_configuration:
            error_handler("ERR_COULD_NOT_GET_OPENID_CONFIGURATION")

        return openid_configuration

    def login(self):
        """Authenticates using device code."""
        client_id = self.config.get("sso_client_id")
        openid_configuration = self.get_openid_configuration()

        if (
            "urn:ietf:params:oauth:grant-type:device_code"
            not in openid_configuration["grant_types_supported"]
        ):
            error_handler("ERR_SSO_DOES_NOT_SUPPORT_DEVICE_CODE")

        device_code_payload = {"client_id": client_id, "scope": "openid"}
        device_code_response = requests.post(
            openid_configuration["device_authorization_endpoint"],
            data=device_code_payload,
            timeout=TIMEOUT,
        )

        if device_code_response.status_code != requests.status_codes.codes.ok:
            error_handler("ERR_GENERATING_DEVICE_CODE")

        device_code_data = device_code_response.json()
        print(
            "A web browser was opened at {}. Please continue the login in the web browser.".format(
                device_code_data["verification_uri_complete"]
            )
        )
        webbrowser.open_new(device_code_data["verification_uri_complete"])

        token_payload = {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": device_code_data["device_code"],
            "client_id": client_id,
        }

        while True:
            token_response = requests.post(
                openid_configuration["token_endpoint"],
                data=token_payload,
                timeout=TIMEOUT,
            )
            token_data = token_response.json()

            if token_response.status_code == requests.status_codes.codes.ok:
                keyring.set_password(
                    "system",
                    "timedctl_token_" + client_id + "_access",
                    token_data["access_token"],
                )
                keyring.set_password(
                    "system",
                    "timedctl_token_" + client_id + "_refresh",
                    token_data["refresh_token"],
                )
                return token_data["access_token"]
            elif token_data["error"] not in ("authorization_pending", "slow_down"):
                print(token_data["error_description"])
                error_handler("ERR_AUTHORIZATION_FAILED")
            else:
                time.sleep(device_code_data["interval"])

    def refresh_token(self, token):
        """Refresh token."""
        client_id = self.config.get("sso_client_id")
        openid_configuration = self.get_openid_configuration()

        if "refresh_token" not in openid_configuration["grant_types_supported"]:
            error_handler("ERR_SSO_DOES_NOT_SUPPORT_REFRESH")

        token_payload = {
            "grant_type": "refresh_token",
            "refresh_token": token,
            "client_id": client_id,
        }
        token_response = requests.post(
            openid_configuration["token_endpoint"], data=token_payload, timeout=TIMEOUT
        )
        token_data = token_response.json()

        if token_response.status_code != requests.status_codes.codes.ok:
            return self.login()

        keyring.set_password(
            "system",
            "timedctl_token_" + client_id + "_access",
            token_data["access_token"],
        )
        return token_data["access_token"]

    def force_renew(self):
        """Force a token renewal."""
        self.oidc_client.autoconfig()
        if self.oidc_client.start_browser_flow():
            if token := self.oidc_client.get_token():
                self.oidc_client.keyring_set(token)
                msg("Token successfully renewed.")
                return
            error_handler("ERR_NO_TOKEN_RENEWAL_FAILED")

    def _get_view(self, initial_view):
        max_key_lengths = [
            max(map(len, col)) for col in zip(*initial_view, strict=False)
        ]
        view = [
            [value.ljust(max_key_lengths[j]) for j, value in enumerate(row)]
            for row in initial_view
        ]
        return view

    def select_report(self, date):
        """FZF prompt to select a report."""
        reports = self.timed.reports.get(
            filters={"date": date},
            include="task,task.project,task.project.customer",
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
                ],
            )
        report_view = self._get_view(report_view)
        # create a list for fzf
        fzf_obj = []
        for row in report_view:
            fzf_obj.append(
                [" | ".join([row[0], row[1], row[2]]), row[1], row[2], row[3], row[4]],
            )

        report = fzf_wrapper(fzf_obj, [0], "Select a report: ")
        return report

    def select_activity(self, date):
        """FZF prompt to select an activity."""
        activities = self.timed.activities.get(filters={"date": date})
        activity_view = []
        # loop through all activities
        for activity_obj in activities:
            # check if there is an actual task, else use an unknown task
            task_data = activity_obj["relationships"]["task"]["data"]
            if task_data:
                task = self.timed.tasks.get(id=task_data["id"], cached=True)
            else:
                task = {"attributes": {"name": "Unknown task"}, "id": None}
            activity_view.append(
                [
                    task["attributes"]["name"],
                    activity_obj["attributes"]["comment"],
                    activity_obj["attributes"]["from-time"].strftime("%H:%M:%S")
                    + " - "
                    + activity_obj["attributes"]["to-time"].strftime("%H:%M:%S"),
                    task["id"],
                    activity_obj["id"],
                ],
            )
        activity_view = self._get_view(activity_view)
        # create a list for fzf
        fzf_obj = []
        for row in activity_view:
            fzf_obj.append(
                [" | ".join([row[0], row[1], row[2]]), row[1], row[2], row[3], row[4]],
            )

        activity_obj = fzf_wrapper(fzf_obj, [0], "Select an activity: ")
        return activity_obj

    def format_activity(self, activity_obj):
        """Format an activity for display."""
        task_obj = activity_obj["relationships"]["task"]

        task = task_obj["attributes"]["name"]

        project_obj = self.timed.projects.get(
            id=task_obj["relationships"]["project"]["id"],
            cached=True,
        )
        project = project_obj["attributes"]["name"]

        customer_obj = self.timed.customers.get(
            id=project_obj["relationships"]["customer"]["data"]["id"],
            cached=True,
        )
        customer = customer_obj["attributes"]["name"]
        return f"{customer} > {project} > {task}"

    def _get_by_name(self, items, name):
        return next(
            (i for i in items if i["attributes"]["name"] == name),
            None,
        )

    def get_customer_by_name(self, customers, name, archived):
        """Get customer by name."""
        customers = self.timed.customers.get(
            cached=True,
            filters={"archived": archived},
        )
        if customer := self._get_by_name(customers, name):
            return customer["id"]
        error_handler("ERR_CUSTOMER_NOT_FOUND")

    def get_project_by_name(self, projects, name, customer_id, archived):
        """Get project by name."""
        projects = self.timed.projects.get(
            cached=True,
            filters={"customer": customer_id, "archived": archived},
        )
        if project := self._get_by_name(projects, name):
            return project["id"]
        error_handler("ERR_PROJECT_NOT_FOUND")

    def get_task_by_name(self, tasks, name, project_id, archived):
        """Get task by name."""
        tasks = self.timed.tasks.get(
            cached=True,
            filters={"project": project_id, "archived": archived},
        )
        if task := self._get_by_name(tasks, name):
            return task["id"]
        error_handler("ERR_TASK_NOT_FOUND")

    def select_task(self, customer, project, task, show_archived):
        """Select a task ID with fzf."""
        # select a customer
        customers = self.timed.customers.get(
            filters={"archived": show_archived},
            cached=True,
        )
        if customer:
            customer_id = self.get_customer_by_name(customers, customer, show_archived)
        else:
            customer_id = fzf_wrapper(
                customers,
                ["attributes", "name"],
                "Select a customer: ",
            )["id"]
        # get projects
        projects = self.timed.projects.get(
            filters={"customer": customer_id, "archived": show_archived},
            cached=True,
        )
        # select a project
        if project:
            project_id = self.get_project_by_name(
                projects,
                project,
                customer_id,
                show_archived,
            )
        else:
            project_id = fzf_wrapper(
                projects,
                ["attributes", "name"],
                "Select a project: ",
            )["id"]
        # get tasks
        tasks = self.timed.tasks.get(
            filters={"project": project_id, "archived": show_archived},
            cached=True,
        )
        # select a task
        if task:
            task_id = self.get_task_by_name(tasks, task, project_id, show_archived)
        else:
            task_id = fzf_wrapper(tasks, ["attributes", "name"], "Select a task: ")[
                "id"
            ]
        return task_id

    def get_customers(self, output_format):
        """Get customers."""
        customers = self.timed.customers.get(cached=True)
        output = [
            {"id": customer["id"], "name": customer["attributes"]["name"]}
            for customer in customers
        ]
        output_formatted(output, output_format)

    def get_projects(self, output_format, customer_id, customer_name, archived):
        """Get projects."""
        if not (customer_id or customer_name):
            error_handler("ERR_MISSING_ARGUMENTS")
        # Get customer ID if name is specified
        if not customer_id:
            customers = self.timed.customers.get(cached=True)
            customer_id = self.get_customer_by_name(customers, customer_name, archived)
        projects = self.timed.projects.get(
            cached=True,
            filters={"customer": customer_id},
        )
        output = [
            {"id": project["id"], "name": project["attributes"]["name"]}
            for project in projects
        ]
        output_formatted(output, output_format)

    def get_tasks(
        self,
        output_format,
        customer_id,
        customer_name,
        project_id,
        project_name,
        archived,
    ):
        """Get tasks."""
        if project_name and not (customer_id or customer_name):
            error_handler("ERR_CUSTOMER_INFO_MISSING")
        if not (project_id or project_name):
            error_handler("ERR_MISSING_ARGUMENTS")
        # Get project ID if name is specified
        if not project_id:
            # we need an id for the customer
            if not customer_id:
                customers = self.timed.customers.get(cached=True)
                customer_id = self.get_customer_by_name(
                    customers,
                    customer_name,
                    archived,
                )
            # get the project id
            projects = self.timed.projects.get(
                cached=True,
                filters={"customer": customer_id},
            )
            project_id = self.get_project_by_name(
                projects,
                project_name,
                customer_id,
                archived,
            )
        # get the tasks for the specified project
        tasks = self.timed.tasks.get(cached=True, filters={"project": project_id})
        output = [
            {"id": task["id"], "name": task["attributes"]["name"]} for task in tasks
        ]
        output_formatted(output, output_format)

    def get_overtime(self, date):
        """Get overtime of user."""
        user = self.timed.users.me["id"]
        overtime = self.timed.overtime.get({"user": user, "date": date})
        msg(f"Current overtime is: {overtime}")

    def get_reports(self, date):
        """Get reports."""
        reports = self.timed.reports.get(
            filters={"date": date},
            include="task,task.project,task.project.customer",
        )
        title = f"Activities for {date if date is not None else 'today'}:"
        table = Table(
            "Customer",
            "Project",
            "Task",
            "Comment",
            "Duration",
            title=title,
            title_style="bold",
            show_lines=True,
        )
        total = timedelta(days=0)
        for report in reports:
            task_obj = report["relationships"]["task"]
            project_obj = task_obj["relationships"]["project"]
            customer_obj = project_obj["relationships"]["customer"]
            # get name attributes
            task, project, customer = (
                x["attributes"]["name"] for x in [task_obj, project_obj, customer_obj]
            )
            comment = report["attributes"]["comment"]
            duration: timedelta = report["attributes"]["duration"]
            total += duration

            table.add_row(customer, project, task, comment, str(duration))
        table.add_row("", "", "", "", str(total))
        print(table)

    def get_activities(self, date):
        """Get activities."""
        activities = self.timed.activities.get(
            filters={"day": date},
            include="task,task.project,task.project.customer",
        )
        title = f"Activities for {date if date is not None else 'today'}:"
        table = Table(
            "Activity",
            "Comment",
            "Start",
            "End",
            title=title,
            title_style="bold",
            show_lines=True,
        )
        total_time = timedelta()
        for activity_obj in activities:
            attributes = activity_obj["attributes"]

            activity_fmt = self.format_activity(activity_obj)
            comment = attributes["comment"]
            from_time_fmt = attributes["from-time"].strftime("%H:%M:%S")

            to_time = attributes["to-time"]
            to_time_fmt = "active"
            if to_time:
                # Format the time if set
                to_time_fmt = to_time.strftime("%H:%M:%S")
                # Temporary timedelta
                tmp_timedelta = to_time - attributes["from-time"]
                # Add the rounded timedelta to the total time
                rounding_factor = timedelta(minutes=15)
                rounded_time = (
                    (tmp_timedelta + rounding_factor - timedelta(seconds=1))
                    // rounding_factor
                    * rounding_factor
                )
                total_time += rounded_time

            table.add_row(activity_fmt, comment, from_time_fmt, to_time_fmt)

        print(table)
        msg(f"Total: {total_time}")

    def delete_report(self, date):
        """Delete report(s)."""
        report = self.select_report(date)
        res = pyfzf.FzfPrompt().prompt(
            ["Yes", "No"],
            f"--prompt 'Are you sure? Delete \"{report[1]}\"?'",
        )
        if res[0] != "Yes":
            error_handler("ERR_DELETION_ABORTED")
        req = self.timed.reports.delete(report[-1])
        if req.status_code != requests.codes["no_content"]:
            error_handler("ERR_DELETION_FAILED")
        msg(f'Deleted report "{report[1]}"')

    def add_report(
        self,
        customer,
        project,
        task,
        description,
        duration,
        show_archived,
    ):
        """Add report(s)."""
        # select a task
        task_id = self.select_task(customer, project, task, show_archived)
        # ask the user to enter a description
        if not description:
            msg("Enter a description")
            # get description
            description = click.prompt("")
        # ask the user to enter a duration
        if duration and re.match(r"^\d{1,2}:\d{2}:\d{2}$", duration) is None:
            error_handler("ERR_INVALID_DURATION")
        else:
            duration = time_picker()
        # create the report
        res = self.timed.reports.post(
            {"duration": duration, "comment": description},
            {
                "task": task_id,
            },
        )
        if res.status_code != requests.codes["created"]:
            error_handler("ERR_REPORT_CREATION_FAILED")
        msg("Report created successfully")

    def edit_report(self, date):
        """Edit report(s)."""
        report = self.select_report(date)

        msg("Comment", True)
        comment = click.prompt("", default=report[1].strip())
        duration = time_picker(default=report[2])
        res = pyfzf.FzfPrompt().prompt(["No", "Yes"], "--prompt 'Are you sure?'")
        if res != ["Yes"]:
            error_handler("ERR_REPORT_UPDATE_ABORTED")
        res = self.timed.reports.patch(
            report[-1],
            {"comment": comment, "duration": duration},
            {"task": report[-2]},
        )
        if res.status_code != requests.codes["ok"]:
            error_handler("ERR_REPORT_UPDATE_FAILED")
        msg("Report updated successfully")

    def start_activity(self, comment, customer, project, task, show_archived, start):
        """Start recording activity."""
        if start:
            # handle invalid input
            if not re.match(r"^(\d{2}:)?\d{2}:\d{2}$", start):
                error_handler("ERR_INVALID_START_TIME")
            # handle short hand time
            if re.match(r"^\d{2}:\d{2}$", start):
                start = f"{start}:00"

        task_id = self.select_task(customer, project, task, show_archived)
        # create the activity
        res = self.timed.activities.start(
            attributes={"comment": comment, "from-time": start},
            relationships={"task": task_id},
        )
        if res.status_code != requests.codes["created"]:
            error_handler("ERR_ACTIVITY_START_FAILED")
        msg(f"Activity {comment} started successfully.")

    def stop_activity(self):
        """Stop current activity."""
        if not self.timed.activities.current:
            error_handler("ERR_NO_CURRENT_ACTIVITY")
        self.timed.activities.stop()
        msg("Activity stopped successfully.")

    def show_activity(self, short):
        """Show current activity."""
        current_activity = self.timed.activities.get(
            filters={"active": True},
            include="task,task.project,task.project.customer",
        )
        if not current_activity:
            error_handler("ERR_NO_CURRENT_ACTIVITY")
        activity_obj = current_activity[0]
        comment = " > " + activity_obj["attributes"]["comment"] if not short else ""
        start = activity_obj["attributes"]["from-time"].strftime("%H:%M:%S")
        msg(
            f"Current activity: {self.format_activity(activity_obj)}{comment}"
            + f"  (Since {start})",
        )

    def restart_activity(self, date):
        """Restart an activity."""
        # stop current activity first
        if self.timed.activities.current:
            self.timed.activities.stop()
            msg("Stopped current activity.")
        # select an activity
        activity_obj = self.select_activity(date)
        # grab attributes
        comment = activity_obj[1]
        task_id = activity_obj[3]
        res = self.timed.activities.start(
            attributes={"comment": comment},
            relationships={"task": task_id},
        )
        if res.status_code != requests.codes["created"]:
            error_handler("ERR_ACTIVITY_START_FAILED")
        msg(f'Activity "{comment}" restarted successfully.')

    def delete_activity(self, date):
        """Delete an activity."""
        # select an activity
        activity_obj = self.select_activity(date)
        if not self.timed.activities.delete(activity_obj[-1]):
            error_handler("ERR_ACTIVITY_DELETE_FAILED")
        msg(f"Activity {activity_obj[1]} deleted successfully.")

    def activity_generate_timesheet(self):
        """Generate the timesheet of the current activities."""
        activities = self.timed.activities.get()
        reports = self.timed.reports.get()
        if not activities:
            error_handler("ERR_NO_ACTIVITIES")
        for activity_obj in activities:
            attr = activity_obj["attributes"]
            if not attr["transferred"]:
                # stop running activities
                if not attr["to-time"]:
                    attr["to-time"] = datetime.now()
                # calculate duration
                duration = attr["to-time"] - attr["from-time"]
                # get task
                task = activity_obj["relationships"]["task"]["data"]["id"]
                # check if there is a report with the same
                # comment that already exists
                report = [
                    x
                    for x in reports
                    if x["attributes"]["comment"] == attr["comment"]
                    and x["relationships"]["task"]["data"]["id"] == task
                ]
                # if report has been found
                if len(report) > 0:
                    report = report[0]
                    # deserialize the timedelta
                    hours, minutes, seconds = report["attributes"]["duration"].split(
                        ":",
                    )
                    old_duration = timedelta(
                        hours=int(hours),
                        minutes=int(minutes),
                        seconds=int(seconds),
                    )
                    # calculate the new duration
                    report["attributes"]["duration"] = old_duration + duration
                    # update report
                    self.timed.reports.patch(
                        report["id"],
                        report["attributes"],
                        {"task": task},
                    )
                else:
                    # create report
                    res = self.timed.reports.post(
                        {
                            "duration": duration,
                            "comment": attr["comment"],
                        },
                        {"task": task},
                    )
                    # append the report to the known reports
                    reports.append(res.json()["data"])
                # update activity to be transferred
                attr["transferred"] = True
                self.timed.activities.patch(
                    activity_obj["id"],
                    attr,
                    {"task": task},
                )
        msg("Timesheet generated successfully.")
