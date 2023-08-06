from click.testing import CliRunner

from timedctl.timedctl import timedctl


def test_current_activity():
    runner = CliRunner()
    result = runner.invoke(timedctl, ["get", "reports"])
    assert result.exit_code == 0
    assert "Reports for today:" in result.output
    result = runner.invoke(timedctl, ["get", "reports", "--date", "2000-01-01"])
    assert result.exit_code == 0
    assert "Reports for 2000-01-01:" in result.output
