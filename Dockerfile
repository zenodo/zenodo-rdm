# syntax=docker/dockerfile:1
#
# Dockerfile that builds a fully functional image of the Zenodo app.
#
# Historically this image was based on the Invenio base image
# (registry.cern.ch/inveniosoftware/almalinux), which shipped Python, Node.js
# and uv ready to go. There is no such base image for Python 3.14 yet, so we
# start from stock almalinux:9 and set up Python (via uv), Node.js + pnpm and
# the system libraries Invenio needs. Single-stage, linux/amd64.
#
# Build:
#   docker build -t zenodo:latest .

ARG PYTHON_VERSION=3.14
ARG NODE_VERSION=24
ARG PNPM_VERSION=11.15.1
# 5.9.6 ships a prebuilt cp314 manylinux wheel on PyPI (no compilation) and
# satisfies xrootdpyfs's xrootd<6.0.0 pin. The wheel bundles the XRootD client
# libraries, so no system XRootD RPMs (and no xrootd repo) are needed.
ARG XROOTD_VERSION=5.9.6

FROM almalinux:9

ARG PYTHON_VERSION
ARG NODE_VERSION
ARG PNPM_VERSION
ARG XROOTD_VERSION
ARG TARGETARCH

# Locale
RUN dnf install -y glibc-langpack-en && dnf clean all
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

# Enable EPEL + CRB (krb5-devel, xmlsec1-devel, ...) and Remi (vips)
RUN dnf install -y dnf-plugins-core epel-release && \
    dnf config-manager --set-enabled crb && \
    dnf install -y http://rpms.remirepo.net/enterprise/remi-release-9.rpm && \
    dnf clean all

# System libraries: build toolchain + runtime deps (single stage keeps both)
RUN --mount=type=cache,target=/var/cache/dnf,sharing=locked,id=dnf-${TARGETARCH} \
    dnf install -y --setopt=install_weak_deps=False \
        gcc gcc-c++ make cmake pkgconf git \
        cairo-devel libffi-devel libpq-devel libxml2-devel libxslt-devel \
        ImageMagick-devel openssl-devel bzip2-devel xz-devel sqlite-devel \
        xmlsec1-devel xmlsec1-openssl-devel \
        krb5-devel krb5-workstation libuuid-devel \
        vips-devel \
        dejavu-sans-fonts

# Node.js + pnpm (baked into the layer so it isn't re-fetched per build)
RUN curl -fsSL https://rpm.nodesource.com/setup_${NODE_VERSION}.x | bash - && \
    dnf install -y --setopt=install_weak_deps=False nodejs && \
    dnf clean all && rm -rf /var/cache/dnf && \
    corepack enable && \
    corepack prepare pnpm@${PNPM_VERSION} --activate

# Kerberos configuration (requests-kerberos / XRootD auth)
COPY ./krb5.conf /etc/krb5.conf

# ---- Instance layout + non-root user (UID 1000, GID 0 for OpenShift) ----
ENV WORKING_DIR=/opt/invenio \
    INVENIO_INSTANCE_PATH=/opt/invenio/var/instance
ARG INVENIO_USER_ID=1000
RUN useradd --uid ${INVENIO_USER_ID} --gid 0 --create-home invenio && \
    mkdir -p ${WORKING_DIR}/src \
             ${INVENIO_INSTANCE_PATH}/data \
             ${INVENIO_INSTANCE_PATH}/archive \
             ${INVENIO_INSTANCE_PATH}/static \
             ${INVENIO_INSTANCE_PATH}/assets
WORKDIR ${WORKING_DIR}/src

# ---- Python via uv (almalinux 9 only ships 3.9) ----
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
ENV UV_PYTHON_INSTALL_DIR=/opt/python
RUN uv python install ${PYTHON_VERSION} && \
    ln -sfn $(uv python find ${PYTHON_VERSION}) /usr/local/bin/python && \
    ln -sfn $(uv python find ${PYTHON_VERSION}) /usr/local/bin/python3

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON=${PYTHON_VERSION} \
    UV_CACHE_DIR=/opt/.cache/uv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_FROZEN=1 \
    UV_REQUIRE_HASHES=1 \
    UV_VERIFY_HASHES=1
ENV PATH="${WORKING_DIR}/src/.venv/bin:${PATH}"

ARG BUILD_EXTRAS="--extra sentry --extra xrootd"

# ---- Python dependencies (no workspace packages yet, for layer caching) ----
# xrootd is installed separately below (self-contained wheel), so exclude it here.
RUN --mount=type=cache,target=/opt/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-dev --no-install-workspace --no-editable ${BUILD_EXTRAS} \
        --no-install-package=xrootd

# ---- Application source + instance configuration ----
COPY . .
COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./translations ${INVENIO_INSTANCE_PATH}/translations

# Install workspace packages (zenodo-rdm, zenodo-legacy)
RUN --mount=type=cache,target=/opt/.cache/uv \
    uv sync --frozen --no-dev ${BUILD_EXTRAS} \
        --no-install-package=xrootd

# XRootD: install the self-contained cp314 wheel after uv sync (which would
# otherwise drop it). UV_REQUIRE_HASHES=0 because it's installed outside the lock.
RUN UV_REQUIRE_HASHES=0 uv pip install --no-cache xrootd==${XROOTD_VERSION}

# Caching is done on a mount; disable it for the remaining filesystem writes.
ENV UV_NO_CACHE=1

# ---- Build frontend assets (pnpm + rspack via invenio-assets) ----
# `invenio webpack buildall` runs create + install + build. invenio-assets ships
# a pnpm-workspace.yaml with `strictDepBuilds: false`, so pnpm 11 does not error
# on the deps whose build scripts it skips (@swc/core, @parcel/watcher, ...). The
# bundles land in the instance static dir, so the whole assets working tree
# (incl. node_modules) is removed in the same layer and never bloats the image.
# The pnpm content store lives on a cache mount for fast rebuilds.
ENV PNPM_STORE_DIR=/opt/.cache/pnpm-store
RUN --mount=type=cache,target=/opt/.cache/pnpm-store \
    cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    invenio collect --verbose && \
    invenio webpack buildall && \
    rm -rf ${INVENIO_INSTANCE_PATH}/assets

# ---- Build metadata ----
ARG IMAGE_BUILD_TIMESTAMP
ARG SENTRY_RELEASE
ENV INVENIO_IMAGE_BUILD_TIMESTAMP="'${IMAGE_BUILD_TIMESTAMP}'" \
    SENTRY_RELEASE=${SENTRY_RELEASE}
RUN echo "Image build timestamp $INVENIO_IMAGE_BUILD_TIMESTAMP"

# Make the tree group-writable (GID 0) so the runtime user can write the instance.
RUN chown -R invenio:0 ${WORKING_DIR} && chmod -R g=u ${WORKING_DIR}

USER invenio
EXPOSE 5000
ENTRYPOINT [ "bash", "-l" ]
