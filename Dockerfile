# syntax=docker/dockerfile:1
#
# Dockerfile that builds a fully functional image of the Zenodo app.
#
# The Invenio base image is used to build the app, but the final image is based on
# `python:3.14-slim-trixie` to reduce the image size.

ARG BUILD_PLATFORM=linux/amd64
ARG BUILD_EXTRAS="--extra sentry --extra xrootd"

FROM --platform=${BUILD_PLATFORM} ghcr.io/inveniosoftware/invenio:debian-python3.14 AS base

ENV PNPM_CONFIG_STORE_DIR=/pnpm/store \
    PNPM_CONFIG_CACHE_DIR=/pnpm/cache

# --- Python dependencies ---
# Install dependencies separately from a requirements.txt export, to avoid busting the
# cache when we bump the app version.
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
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN --mount=type=cache,target=/pnpm/store \
    --mount=type=cache,target=/pnpm/cache \
    pnpm install --frozen-lockfile --ignore-scripts \
        --config.node-linker=hoisted --shamefully-hoist

# --- Build stage ---
FROM base AS builder

# Additional libraries needed to build Zenodo's Python dependencies.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
        cmake \
        libkrb5-dev \
        libvips-dev \
        libxmlsec1-dev \
        libxmlsec1-openssl \
        pkg-config \
        uuid-dev

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
# Git requirements are pinned to commits but do not have archive hashes; registry
# requirements still carry and verify their exported hashes.
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

# --- Frontend assets ---
# Fail if the generated project differs from the one used to install dependencies.
RUN mkdir -p ${INVENIO_INSTANCE_PATH}/assets && \
    cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    invenio collect --verbose && \
    invenio webpack create && \
    cmp package.json ${INVENIO_INSTANCE_PATH}/assets/package.json
COPY pnpm-lock.yaml ${INVENIO_INSTANCE_PATH}/assets/pnpm-lock.yaml
COPY --from=frontend-dependencies /frontend/node_modules ${INVENIO_INSTANCE_PATH}/assets/node_modules

# We need to run postinstall, since when we run pnpm install in the
# "frontend-dependencies" stage, we didn't have the assets dir with the necessary
# patch-package patches. The supply-chain policy check runs on the install in
# "frontend-dependencies".
ENV PNPM_CONFIG_VERIFY_DEPS_BEFORE_RUN=false
RUN --mount=type=cache,target=/pnpm/store \
    --mount=type=cache,target=/pnpm/cache \
    cd ${INVENIO_INSTANCE_PATH}/assets && \
    pnpm run postinstall && \
    invenio webpack build && \
    rm -rf ${INVENIO_INSTANCE_PATH}/assets

# The instance must be group-writable, since the container can run under an arbitrary
# UID in GID 0. Done here rather than in the final image, where a recursive chown would
# duplicate the whole tree into a second layer; COPY --from preserves owner and mode.
RUN chown -R invenio:0 ${WORKING_DIR} && chmod -R g=u ${WORKING_DIR}

# --- Application image ---
# Must stay on the same Python and Debian release as the base image above, so that the
# venv and its compiled extensions still match.
FROM --platform=${BUILD_PLATFORM} python:3.14-slim-trixie

# Shared libraries the venv links against: libvips42t64 pulls in the image-format ones,
# the rest cover uwsgi, python-gssapi and Kerberos auth. wand and cairocffi open
# libMagickWand and libcairo through ctypes, so those two are named here rather than
# left to libvips' dependency tree. procps provides ps/top/pkill/watch for interactive
# shells in a running container.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --yes --no-install-recommends \
        ca-certificates \
        curl \
        fonts-dejavu \
        krb5-user \
        libcairo2 \
        libgssapi-krb5-2 \
        libmagickwand-7.q16-10 \
        libpcre2-8-0 \
        libuuid1 \
        libvips42t64 \
        libxml2 \
        locales \
        procps

RUN localedef -i en_US -c -f UTF-8 -A /usr/share/locale/locale.alias en_US.UTF-8

ENV WORKING_DIR=/opt/invenio \
    INVENIO_INSTANCE_PATH=/opt/invenio/var/instance \
    INVENIO_USER_ID=1000 \
    PATH=/opt/invenio/src/.venv/bin:${PATH} \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_NO_CACHE=1

RUN useradd invenio --uid 1000 --gid 0 && \
    mkdir -p ${WORKING_DIR} && \
    chown invenio:0 ${WORKING_DIR} && \
    chmod g=u ${WORKING_DIR}

# Kerberos configuration (requests-kerberos / XRootD auth)
COPY ./krb5.conf /etc/krb5.conf

# The venv has no pip, so `uv pip list` and friends are the only way to inspect the
# installed dependencies from inside a running container.
COPY --from=base /bin/uv /bin/uvx /bin/

COPY --from=builder ${WORKING_DIR} ${WORKING_DIR}

# --- Build metadata ---
ARG IMAGE_BUILD_TIMESTAMP
ARG SENTRY_RELEASE
ENV INVENIO_IMAGE_BUILD_TIMESTAMP="'${IMAGE_BUILD_TIMESTAMP}'" \
    SENTRY_RELEASE=${SENTRY_RELEASE}

WORKDIR ${WORKING_DIR}/src
USER invenio
EXPOSE 5000
ENTRYPOINT [ "bash", "-c" ]
