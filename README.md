<div align="center">
  <img width="500" src="https://about.zenodo.org/static/img/logos/zenodo-black-border.svg">
</div>

[![](https://img.shields.io/travis/zenodo/zenodo-rdm.svg)](https://travis-ci.org/zenodo/zenodo-rdm)
[![](https://img.shields.io/coveralls/zenodo/zenodo-rdm.svg)](https://coveralls.io/r/zenodo/zenodo-rdm)
[![](https://img.shields.io/github/license/zenodo/zenodo-rdm.svg)](https://github.com/zenodo/zenodo-rdm/blob/master/LICENSE)

Zenodo Invenio RDM instance.

## Development

To get started you need to have
[`invenio-cli`](https://github.com/inveniosoftware/invenio-cli/) installed (we
recommend using [`pipx`](https://github.com/pipxproject/pipx) to do so).

```bash
# Install dependencies
pipenv sync --dev
pipenv run pip install -r requirements-devel.txt

# Build assets
invenio-cli update --install-js

# Start services (DB, ES, etc.). Use the "--force" option to recreate
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

## Docker images

The repository is setup via GitHub actions to automatically build [Docker
images](https://github.com/zenodo/zenodo-rdm/packages/157045):

- `zenodo-rdm:${VERSION}` when tags in the format `v${VERSION}` are pushed
- `zenodo-rdm:latest` when the `master` branch is updated

To manually build the `latest` image, e.g. in case you update a development
dependency, you can trigger a [repository
dispatch](https://help.github.com/en/actions/reference/events-that-trigger-workflows#external-events-repository_dispatch)
in the following way:

```bash
# First, you need a GitHub personal access token with no scopes from
# https://github.com/settings/tokens/new.
read -s GH_TOKEN

curl -H "Accept: application/vnd.github.everest-preview+json" \
    -H "Authorization: token $GH_TOKEN" \
    --request POST \
    --data '{"event_type": "publish-latest"}' \
    https://api.github.com/repos/zenodo/zenodo-rdm/dispatches
```
