from click.testing import CliRunner

from timedctl.timedctl import timedctl


def test_get_reports():
    runner = CliRunner()
    result = runner.invoke(timedctl, ["get", "reports"])
    assert result.exit_code == 0
    assert "Reports for today:" in result.output
    result = runner.invoke(timedctl, ["get", "reports", "--date", "2000-01-01"])
    assert result.exit_code == 0
    assert "Reports for 2000-01-01:" in result.output


def test_get_activities():
    runner = CliRunner()
    result = runner.invoke(timedctl, ["get", "activities", "--date", "2000-01-01"])
    assert result.exit_code == 0
    assert "Activities for 2000-01-01:" in result.output
    result = runner.invoke(timedctl, ["get", "activities"])
    assert result.exit_code == 0
    assert "Activities for today:" in result.output


def test_get_overtime():
    runner = CliRunner()
    result = runner.invoke(timedctl, ["get", "overtime"])
    assert result.exit_code == 0
    assert "Current overtime" in result.output


def test_get_absences():
    runner = CliRunner()
    result = runner.invoke(timedctl, ["get", "absences"])
    assert result.exit_code == 1
    assert "ERR" in result.output
