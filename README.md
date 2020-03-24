<div align="center">
  <img width="500" src="https://about.zenodo.org/static/img/logos/zenodo-black-border.svg">
</div>

[![](https://img.shields.io/travis/zenodo/zenodo-rdm.svg)](https://travis-ci.org/zenodo/zenodo-rdm)
[![](https://img.shields.io/coveralls/zenodo/zenodo-rdm.svg)](https://coveralls.io/r/zenodo/zenodo-rdm)
[![](https://img.shields.io/github/license/zenodo/zenodo-rdm.svg)](https://github.com/zenodo/zenodo-rdm/blob/master/LICENSE)

Zenodo Invenio RDM instance.

## Development

To get started you need to have [`invenio-cli`](https://github.com/inveniosoftware/invenio-cli/) installed (we recommend using [`pipx`](https://github.com/pipxproject/pipx) to do so).

```bash
# Install dependencies and build assets
pipenv install --dev
pipenv run pip install -r requirements-devel.txt
# XXX: Remove after https://github.com/inveniosoftware/invenio-cli/issues/121 has been fixed
cur_dir="$(pwd)"
venv_dir="$(pipenv --venv)"
sed -i -E "s|^project_dir = .+|project_dir = $cur_dir|" .invenio
sed -i -E "s|^logfile = .+|logfile = $cur_dir/logs/invenio-cli.log|" .invenio
sed -i -E "s|^instance_path = .+|instance_path = $venv_dir/var/instance|" .invenio
# Symlink templates and config
ln -sv "$(realpath templates)" "$venv_dir/var/instance/templates"
ln -sv "$(realpath invenio.cfg)" "$venv_dir/var/instance/invenio.cfg"
# Build assets
invenio-cli update --install-js
# Start services (DB, ES, etc.)
invenio-cli services
# Run it
invenio-cli run

# For using local repositories (e.g. invenio-communities):
# Activate the virtualenv
pipenv shell
# Go to your local repo
cd ~/src/invenio-communities
# Uninstall the dependency
pip uninstall -y invenio-communities
# Install the local source
pip install -e .
```
