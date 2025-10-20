<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://about.zenodo.org/static/img/logos/zenodo-white-border.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://about.zenodo.org/static/img/logos/zenodo-black-border.svg">
    <img alt="Zenodo logo" src="https://about.zenodo.org/static/img/logos/zenodo-white-border.svg" width="500">
  </picture>
</div>

## Development quick start

Make sure you have [`uv` installed](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer), and then run the following commands:

```bash
uv tool install invenio-cli
invenio-cli check-requirements --development
invenio-cli install
invenio-cli services setup
invenio-cli run
```

### Update dependencies

To update dependencies you need to:

1. Run `invenio-cli packages lock`
2. (Optional) Use [`changelog.py`](https://github.com/slint/changelog.py) to generate the commit message via `changelog.py --package-filter "^invenio" --show-major-bumps --since HEAD`
3. Commit the updated `uv.lock`

> [!TIP]
> To selectively update a specific package, you can use:
>
> ```bash
> uv lock --upgrade-package <package-name>
> ```
