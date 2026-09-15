# Locust load tests


## 1. Install

```bash
# Install + cache on tmp env
uv run --with locust locust --version

# Run commands
uv run --with locust <command>

# Or install on env
uv pip install locust
```

## 2. Initial configuration

### 2.1 Users
There is a wrapper for `invenio users create` that loops `n` times and provides active and confirmed users, they get saved in `accounts.csv` (gitignored)

Example:
```bash
# Local dev environment
./provision_accounts.sh 20
```

**TODO** Run on dev.zenodo.org 

After login (first run) this accounts will add data to `session_cache.json` so that they don't need to login on every run. This is done because login-in users is very slow (by design by any hashing algorithm).

If you have some users created alrready you can manually fill the `accounts.csv` file with the format:
```csv
email,password
locust-1@demo.org,Iv6LCXJBXlzyXEmegbREefPV
```


### 2.2 ENV (local)
Run the project locally without rate limits:
```bash
export INVENIO_RATELIMIT_ENABLED=False; export INVENIO_ACCOUNTS_LOGIN_RATELIMIT=False; invenio-cli run
```

## 3. Run

> **⚠️ Exception** <br>
> Don't try and run `iiif.py` with `--host={SOMETHING}` Since it takes it from `manifest.json` file.

Run scenario blueprint:
```bash
uv run --with locust locust -f <file_path.py> \
--host <https://127.0.0.1:5000 | https://dev.zenodo.org> \
--headless -u 10 -r 2 -t 5m
# -u --> num of users
# -r --> num of users to spawn per second
# -t --> time to run the scenario
```

> **`"-r"` is important to have in mind, if we don't have a `session_cache.json` file with some data, it is better to have a low spawn rate of users or we will create a login storm.**

Example read load:
```
uv run --with locust locust -f reads.py \
--host=https://127.0.0.1:5000 \
--headless -u 20 -r 2 -t 5m
```

Example write load:
```
uv run --with locust locust -f writes.py \
--host=https://127.0.0.1:5000 \
--headless -u 6 -r 1 -t 5m
```

If you have lots of ram you can edit `_SIZE_TIERS` in the `common.py` file to upload bigger files.
Then change this line:
```python
    @task(1)  # Be careful with this one you can crash your own computer
# to thid:
    @task(10)  # Be careful with this one you can crash your own computer
```

Run a combo of both write and read:
```
uv run --with locust locust -f writes_and_reads.py \
--host=https://127.0.0.1:5000 \
--headless -u 6 -r 1 -t 5m
```

### 3.1 Monitor

#### 3.1.1 Local monitor

One of the things to check is the resources used by docker containers while running the tests:
```bash
docker stats
```
