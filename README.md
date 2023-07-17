# timedctl
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)


Click TUI for [Timed](https://github.com/adfinis/timed-frontend) using [libtimed](https://github.com/adfinis/libtimed).

## Getting started
Build the project with `poetry build` and install it with `pip install dist/timedctl-*.whl`. You should now be able to use `timedctl` iin your terminal.

## Configuration
Create a config file at `$XDG_CONFIG_HOME/timedctl/config.toml`.
The following values must be set:
```toml
username = "<your username>"
oidc_client_id = "<your oidc client id>"
oidc_auth_endpoint = "<your oidc auth endpoint>"
oidc_token_endpoint = "<your oidc token endpoint>"
```

## License
Code released under the [GNU Affero General Public License v3.0](LICENSE).
