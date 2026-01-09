# syntax=docker/dockerfile:1
#
# Zenodo Production Dockerfile
#
# Uses multi-stage build with Invenio base images:
#   - Builder stage: compiles Python wheels, builds frontend assets
#   - Runtime stage: minimal production image
#
# Note: XRootD (CERN storage) is only available for amd64, so this image
# must be built with --platform=linux/amd64.
#
# Build:
#   docker build --platform=linux/amd64 -t zenodo:latest .
#
# Build with specific options:
#   docker build --platform=linux/amd64 \
#     --build-arg XROOTD_VERSION=5.9.1 \
#     --build-arg SENTRY_RELEASE=$(git rev-parse HEAD) \
#     -t zenodo:$(git rev-parse --short HEAD) .

# Global ARGs (available in all stages)
ARG INVENIO_BASE_VERSION=1
ARG REGISTRY=registry.cern.ch/inveniosoftware
ARG XROOTD_VERSION=5.9.1

# =============================================================================
# STAGE 1: Build Python wheels and frontend assets
# =============================================================================
FROM ${REGISTRY}/almalinux:${INVENIO_BASE_VERSION}-builder AS builder

# Re-declare ARG after FROM to use in this stage
ARG XROOTD_VERSION

# ---- Build dependencies (combined for fewer layers) ----
# - cmake, libuuid-devel: build xrootd Python bindings from PyPI
# - krb5-devel: build kerberos bindings
# - vips-devel: image processing
# - xrootd-client-*: C libraries to link against
RUN dnf config-manager --add-repo https://cern.ch/xrootd/xrootd.repo && \
    dnf install -y http://rpms.remirepo.net/enterprise/remi-release-9.rpm && \
    dnf install -y \
        cmake \
        krb5-devel \
        libuuid-devel \
        vips-devel \
        xrootd-client-devel-${XROOTD_VERSION} \
        xrootd-client-libs-${XROOTD_VERSION} && \
    dnf clean all

# ---- Python and uv configuration ----
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/opt/.cache/uv \
    UV_COMPILE_BYTECODE=1 \
    UV_FROZEN=1 \
    UV_LINK_MODE=copy \
    UV_REQUIRE_HASHES=1 \
    UV_VERIFY_HASHES=1

# ---- Build Python dependencies ----
ARG BUILD_EXTRAS="--extra sentry --extra xrootd"

# Install dependencies (not the workspace packages yet)
# Using bind mounts avoids creating a layer for pyproject.toml/uv.lock
RUN --mount=type=cache,target=/opt/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-dev --no-install-workspace --no-editable ${BUILD_EXTRAS} \
        --no-install-package=xrootd

# Add venv to PATH for subsequent commands
ENV PATH="${WORKING_DIR}/src/.venv/bin:${PATH}"

# Build xrootd from PyPI BEFORE copying source (slow step, rarely changes)
# Must link against system xrootd-client libs installed above
RUN UV_REQUIRE_HASHES=0 uv pip install --no-cache xrootd==${XROOTD_VERSION}

# Copy source code
COPY . .

# Install workspace packages (zenodo-rdm, zenodo-legacy)
RUN --mount=type=cache,target=/opt/.cache/uv \
    uv sync --frozen --no-dev ${BUILD_EXTRAS} \
        --no-install-package=xrootd

# Disable uv cache for subsequent commands (filesystem permission reasons)
ENV UV_NO_CACHE=1

# ---- Build frontend assets ----
# Copy static files and assets BEFORE invenio collect
# webpack buildall = create + install + build
RUN --mount=type=cache,target=/root/.npm \
    cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    invenio collect --verbose && \
    invenio webpack buildall

# =============================================================================
# STAGE 2: Production runtime image
# =============================================================================
FROM ${REGISTRY}/almalinux:${INVENIO_BASE_VERSION}-runtime AS production

# Re-declare ARG after FROM to use in this stage
ARG XROOTD_VERSION

# ---- Runtime dependencies (combined for fewer layers) ----
# - krb5-*: Kerberos authentication
# - vips: image processing (libs only, no -devel)
# - xrootd-client-*: CERN storage client
RUN dnf config-manager --add-repo https://cern.ch/xrootd/xrootd.repo && \
    dnf install -y http://rpms.remirepo.net/enterprise/remi-release-9.rpm && \
    dnf install -y \
        krb5-libs \
        krb5-workstation \
        vips \
        xrootd-client-${XROOTD_VERSION} \
        xrootd-client-libs-${XROOTD_VERSION} && \
    dnf clean all && \
    rm -rf /var/cache/dnf

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
