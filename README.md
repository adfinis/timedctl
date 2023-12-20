# timedctl
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)


Click TUI for [Timed](https://github.com/adfinis/timed-frontend) using [libtimed](https://github.com/adfinis/libtimed).

## Installing
There are currently only packages for arch linux available in the [AUR](https://aur.archlinux.org/packages/timedctl/).
```bash
$ yay -S timedctl
```
People on other distributions can use pip to install the package from pypi:
```bash
$ pip install timedctl
```
Nix / NixOS people can just run the flake:
```
nix run github:adfinis/timedctl
```

### Shell completion
`timedctl` support shell completion for the unaliased commands:

**bash**
```bash
_TIMEDCTL_COMPLETE=bash_source timedctl >> ~/.bashrc
```

**zsh**
```bash
_TIMEDCTL_COMPLETE=zsh_source timedctl >> ~/.zshrc
```

**fish**
```bash
_TIMEDCTL_COMPLETE=fish_source timedctl >  ~/.config/fish/completions/timedctl.fish
```

## Local development
Clone the repository and install the dependencies with `poetry install`. You can now run the project with `poetry run timedctl`. For building wheels, you can use `poetry build`.
Run tests with `poetry run pytest --cov --cov-fail-under 100`.

## Known issues
* Make sure to have a polkit-agent running, otherwise the poetry installation during the installation on arch might fail.
* You need a keyring installed in order for timedctl to store the SSO token, for example `gnome-keyring`.

## Feature roadmap
- [x] SSO auth
- [x] Overtime
- [x] Reports
    - [x] Get
    - [x] Add
    - [x] Delete
    - [x] Update
- [x] Activities
    - [x] Start
    - [x] Stop
    - [x] Delete
    - [x] Restart
- [ ] Absences
    - [ ] Get
    - [ ] Add
    - [ ] Delete
    - [ ] Update
- [ ] Holidays
    - [ ] Get
    - [ ] Add
    - [ ] Delete
    - [ ] Update

## Configuration
Your config file should already be created on the first launch under `$XDG_CONFIG_HOME/timedctl/config.toml`.
If this isn't the case you can see the default config options below:
```toml
username = "<your username>"
timed_url = "<timed url>"
sso_url = "<sso url>"
sso_realm = "<sso realm>"
sso_client_id = "<client id>"
```

## License
Code released under the [GNU Affero General Public License v3.0](LICENSE).
