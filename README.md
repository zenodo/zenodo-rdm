<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://about.zenodo.org/static/img/logos/zenodo-white-border.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://about.zenodo.org/static/img/logos/zenodo-black-border.svg">
    <img alt="Zenodo logo" src="https://about.zenodo.org/static/img/logos/zenodo-white-border.svg" width="500">
  </picture>
</div>

## Deployment instructions

Need to set up the following config variables:

``` python
# Invenio-App-RDM
RDM_RECORDS_USER_FIXTURE_PASSWORDS = {
    'admin@inveniosoftware.org': '123456'
}

# Invenio-Records-Resources
SITE_UI_URL = "https://127.0.0.1:5000"
SITE_API_URL = "https://127.0.0.1:5000/api"

# Invenio-RDM-Records
RDM_RECORDS_DOI_DATACITE_USERNAME = ""
RDM_RECORDS_DOI_DATACITE_PASSWORD = ""
RDM_RECORDS_DOI_DATACITE_PREFIX = ""

# Invenio-OAuthclient
# secrets will be injected on deployment
CERN_APP_CREDENTIALS = {
    "consumer_key": "CHANGE ME",
    "consumer_secret": "CHANGE ME",
}
ORCID_APP_CREDENTIALS = {
    "consumer_key": "CHANGE ME",
    "consumer_secret": "CHANGE ME",
}
```

## Development quick start

```
pip install invenio-cli
invenio-cli check-requirements --development
invenio-cli install
invenio-cli services setup
invenio-cli run
```

See the [InvenioRDM Documentation](https://inveniordm.docs.cern.ch/install/)
for further installation options.

### Update dependencies


To update dependencies you need to:

1. Run `invenio-cli packages lock`
2. (Optional) Use [`changelog.py`](https://github.com/slint/changelog.py) to generate the commit message via `changelog.py --package-filter "^invenio" --show-major-bumps --since HEAD`
3. Commit the updated `uv.lock`
