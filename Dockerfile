# syntax=docker/dockerfile:1
#
# Dockerfile that builds a fully functional image of the Zenodo app.
#
# The Invenio base image provides Python 3.14, Node.js, pnpm, uv and the common
# system libraries and instance layout used by Invenio applications.
#
# Build:
#   docker build -t zenodo:latest .

ARG BUILD_PLATFORM=linux/amd64
ARG BUILD_EXTRAS="--extra sentry --extra xrootd"
ARG PNPM_VERSION=11.15.1

FROM --platform=${BUILD_PLATFORM} ghcr.io/inveniosoftware/invenio:debian-python3.14 AS base

# --- Python dependencies ---
# Export dependencies separately from the application packages. Version-only
# changes produce the same output, allowing BuildKit to reuse the install layer.
FROM base AS python-requirements
ARG BUILD_EXTRAS
RUN --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv export --frozen --no-dev --no-emit-workspace \
        --no-header --no-annotate ${BUILD_EXTRAS} \
        --output-file=/python-requirements.txt >/dev/null

# --- Frontend dependencies ---
FROM base AS frontend-dependencies
ARG PNPM_VERSION
WORKDIR /frontend
RUN npm install --global pnpm@${PNPM_VERSION}
COPY package.json pnpm-lock.yaml ./
RUN --mount=type=cache,target=/opt/.cache/pnpm-store \
    pnpm install --frozen-lockfile --ignore-scripts \
        --config.node-linker=hoisted --shamefully-hoist \
        --store-dir=/opt/.cache/pnpm-store

# --- Application image ---
FROM base

# Additional build and runtime libraries needed by Zenodo.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
        cmake \
        krb5-user \
        libkrb5-dev \
        libvips-dev \
        libxmlsec1-dev \
        libxmlsec1-openssl \
        pkg-config \
        uuid-dev

# Kerberos configuration (requests-kerberos / XRootD auth)
COPY ./krb5.conf /etc/krb5.conf

# The base image creates the instance layout and the UID 1000/GID 0 user.
RUN mkdir -p ${INVENIO_INSTANCE_PATH}/assets

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON=3.14 \
    UV_CACHE_DIR=/opt/.cache/uv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_REQUIRE_HASHES=1 \
    UV_VERIFY_HASHES=1

ARG BUILD_EXTRAS

# --- Python installation ---
COPY --from=python-requirements /python-requirements.txt /tmp/python-requirements.txt
# Git requirements are pinned to commits but do not have archive hashes;
# registry requirements still carry and verify their exported hashes.
RUN --mount=type=cache,target=/opt/.cache/uv \
    uv venv && \
    UV_REQUIRE_HASHES=0 uv pip sync --strict /tmp/python-requirements.txt

# --- Application source ---
COPY . .
COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./translations ${INVENIO_INSTANCE_PATH}/translations

# Install workspace packages (zenodo-rdm, zenodo-legacy)
RUN --mount=type=cache,target=/opt/.cache/uv \
    uv sync --locked --no-dev ${BUILD_EXTRAS}

# Caching is done on a mount; disable it for the remaining filesystem writes.
ENV UV_NO_CACHE=1

# --- Frontend assets ---
# Fail if the generated project differs from the one used to install dependencies.
RUN cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    invenio collect --verbose && \
    invenio webpack create && \
    cmp package.json ${INVENIO_INSTANCE_PATH}/assets/package.json
COPY --from=frontend-dependencies /frontend/node_modules ${INVENIO_INSTANCE_PATH}/assets/node_modules
# The manifest was verified above. Skip pnpm's dependency check, which would
# reinstall the copied node_modules because the generated project has no lockfile.
RUN cd ${INVENIO_INSTANCE_PATH}/assets && \
    ./node_modules/.bin/patch-package && \
    PNPM_CONFIG_VERIFY_DEPS_BEFORE_RUN=false invenio webpack build && \
    rm -rf ${INVENIO_INSTANCE_PATH}/assets

# --- Build metadata ---
ARG IMAGE_BUILD_TIMESTAMP
ARG SENTRY_RELEASE
ENV INVENIO_IMAGE_BUILD_TIMESTAMP="'${IMAGE_BUILD_TIMESTAMP}'" \
    SENTRY_RELEASE=${SENTRY_RELEASE}
RUN echo "Image build timestamp $INVENIO_IMAGE_BUILD_TIMESTAMP"

# OpenShift runs with an arbitrary UID in GID 0, so the instance must be group-writable.
RUN chown -R invenio:0 ${WORKING_DIR} && chmod -R g=u ${WORKING_DIR}

USER invenio
EXPOSE 5000
ENTRYPOINT [ "bash", "-c" ]
