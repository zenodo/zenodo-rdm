# syntax=docker/dockerfile:1
#
# Zenodo Production Dockerfile (Standalone)
#
# Single self-contained build for linux/amd64 with XRootD support.
#
# Build:
#   docker build -t zenodo:latest .
#
# Build with specific options:
#   docker build \
#     --build-arg XROOTD_VERSION=5.9.1 \
#     --build-arg SENTRY_RELEASE=$(git rev-parse HEAD) \
#     -t zenodo:$(git rev-parse --short HEAD) .

# =============================================================================
# Global ARGs
# =============================================================================
ARG LINUX_VERSION=9
ARG PYTHON_VERSION=3.14
ARG NODE_VERSION=22
ARG XROOTD_VERSION=5.9.1

# =============================================================================
# BASE: Common configuration shared by all stages
# =============================================================================
FROM almalinux:${LINUX_VERSION} AS base

ARG PYTHON_VERSION

# Locale configuration
RUN dnf install -y glibc-langpack-en && \
    dnf clean all

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

# Python configuration
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1

# Working directory structure
ENV WORKING_DIR=/opt/invenio \
    INVENIO_INSTANCE_PATH=/opt/invenio/var/instance

# Create invenio user (UID 1000 for compatibility)
ARG INVENIO_USER_ID=1000
RUN useradd --uid ${INVENIO_USER_ID} --gid 0 --create-home invenio

# Create directory structure
RUN mkdir -p ${WORKING_DIR}/src \
             ${INVENIO_INSTANCE_PATH}/data \
             ${INVENIO_INSTANCE_PATH}/archive \
             ${INVENIO_INSTANCE_PATH}/static && \
    chown -R invenio:0 ${WORKING_DIR} && \
    chmod -R g=u ${WORKING_DIR}

WORKDIR ${WORKING_DIR}/src

# Install uv for Python management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Install Python via uv
ENV UV_PYTHON_INSTALL_DIR=/opt/python
RUN uv python install ${PYTHON_VERSION} && \
    ln -sfn $(uv python find ${PYTHON_VERSION}) /usr/local/bin/python && \
    ln -sfn $(uv python find ${PYTHON_VERSION}) /usr/local/bin/python3

# uv configuration
ENV UV_PYTHON=${PYTHON_VERSION} \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# =============================================================================
# BUILDER: Full toolchain for compiling Python/Node.js packages
# =============================================================================
FROM base AS builder

ARG NODE_VERSION
ARG XROOTD_VERSION
ARG TARGETARCH

# Enable EPEL and CRB
RUN dnf install -y dnf-plugins-core && \
    dnf config-manager --set-enabled crb && \
    dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm && \
    dnf clean all

# Add XRootD and Remi repos
RUN dnf config-manager --add-repo https://cern.ch/xrootd/xrootd.repo && \
    dnf install -y http://rpms.remirepo.net/enterprise/remi-release-9.rpm

# Install build tools and development libraries
RUN --mount=type=cache,target=/var/cache/dnf,sharing=locked,id=dnf-${TARGETARCH} \
    dnf install -y --setopt=install_weak_deps=False \
        # Build essentials
        gcc \
        gcc-c++ \
        make \
        cmake \
        pkgconf \
        # Development libraries
        cairo-devel \
        libffi-devel \
        libpq-devel \
        libxml2-devel \
        libxslt-devel \
        ImageMagick-devel \
        openssl-devel \
        bzip2-devel \
        xz-devel \
        sqlite-devel \
        xmlsec1-devel \
        xmlsec1-openssl-devel \
        # Zenodo-specific build deps
        krb5-devel \
        libuuid-devel \
        vips-devel \
        xrootd-client-devel-${XROOTD_VERSION} \
        xrootd-client-libs-${XROOTD_VERSION} \
        # Other
        git \
        dejavu-sans-fonts

# Install Node.js
RUN curl -fsSL https://rpm.nodesource.com/setup_${NODE_VERSION}.x | bash - && \
    dnf install -y --setopt=install_weak_deps=False nodejs && \
    dnf clean all && \
    rm -rf /var/cache/dnf && \
    corepack enable

# ---- Python and uv configuration ----
ENV UV_CACHE_DIR=/opt/.cache/uv \
    UV_FROZEN=1 \
    UV_REQUIRE_HASHES=1 \
    UV_VERIFY_HASHES=1

# ---- Build Python dependencies ----
ARG BUILD_EXTRAS="--extra sentry --extra xrootd"

# Install dependencies (not the workspace packages yet)
RUN --mount=type=cache,target=/opt/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-dev --no-install-workspace --no-editable ${BUILD_EXTRAS} \
        --no-install-package=xrootd

# Add venv to PATH
ENV PATH="${WORKING_DIR}/src/.venv/bin:${PATH}"

# Copy source code
COPY . .

# Install workspace packages (zenodo-rdm, zenodo-legacy)
RUN --mount=type=cache,target=/opt/.cache/uv \
    uv sync --frozen --no-dev ${BUILD_EXTRAS} \
        --no-install-package=xrootd

# Build xrootd from PyPI AFTER uv sync (uv sync removes non-locked packages)
RUN UV_REQUIRE_HASHES=0 uv pip install --no-cache xrootd==${XROOTD_VERSION}

# Disable uv cache for subsequent commands
ENV UV_NO_CACHE=1

# ---- Build frontend assets ----
RUN --mount=type=cache,target=/root/.npm \
    cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    invenio collect --verbose && \
    invenio webpack buildall

# =============================================================================
# PRODUCTION: Minimal runtime image
# =============================================================================
FROM base AS production

ARG XROOTD_VERSION
ARG TARGETARCH

# Enable EPEL and CRB
RUN dnf install -y dnf-plugins-core && \
    dnf config-manager --set-enabled crb && \
    dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm && \
    dnf clean all

# Add XRootD and Remi repos
RUN dnf config-manager --add-repo https://cern.ch/xrootd/xrootd.repo && \
    dnf install -y http://rpms.remirepo.net/enterprise/remi-release-9.rpm

# Install runtime-only system libraries
RUN --mount=type=cache,target=/var/cache/dnf,sharing=locked,id=dnf-${TARGETARCH} \
    dnf install -y --setopt=install_weak_deps=False \
        # Runtime libraries
        cairo \
        libffi \
        libpq \
        libxml2 \
        libxslt \
        ImageMagick-libs \
        openssl-libs \
        bzip2-libs \
        xz-libs \
        sqlite-libs \
        xmlsec1 \
        xmlsec1-openssl \
        # Zenodo-specific runtime deps
        krb5-libs \
        krb5-workstation \
        vips \
        xrootd-client-${XROOTD_VERSION} \
        xrootd-client-libs-${XROOTD_VERSION} \
        # Fonts and utilities
        dejavu-sans-fonts \
        git

# ---- Copy configuration files ----
COPY ./krb5.conf /etc/krb5.conf

# ---- Copy Python environment from builder ----
COPY --from=builder ${WORKING_DIR}/src/.venv ${WORKING_DIR}/src/.venv
ENV PATH="${WORKING_DIR}/src/.venv/bin:${PATH}"

# ---- Copy application code ----
COPY --chown=invenio:0 legacy ./legacy
COPY --chown=invenio:0 site ./site

# ---- Copy instance configuration ----
COPY --chown=invenio:0 ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY --chown=invenio:0 ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY --chown=invenio:0 ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY --chown=invenio:0 ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY --chown=invenio:0 ./translations ${INVENIO_INSTANCE_PATH}/translations

# ---- Copy built static assets from builder ----
COPY --from=builder --chown=invenio:0 ${INVENIO_INSTANCE_PATH}/static ${INVENIO_INSTANCE_PATH}/static
COPY --from=builder --chown=invenio:0 ${WORKING_DIR}/src/static ./static

# ---- Build metadata ----
ARG IMAGE_BUILD_TIMESTAMP
ARG SENTRY_RELEASE

ENV INVENIO_IMAGE_BUILD_TIMESTAMP="'${IMAGE_BUILD_TIMESTAMP}'" \
    SENTRY_RELEASE=${SENTRY_RELEASE}

# ---- Labels ----
LABEL org.opencontainers.image.title="Zenodo" \
      org.opencontainers.image.description="Zenodo Research Data Repository" \
      org.opencontainers.image.source="https://github.com/zenodo/zenodo-rdm" \
      org.opencontainers.image.vendor="CERN" \
      org.opencontainers.image.revision="${SENTRY_RELEASE}"

# ---- Runtime configuration ----
USER invenio
WORKDIR ${WORKING_DIR}/src
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ping || exit 1

ENTRYPOINT ["bash", "-l"]
