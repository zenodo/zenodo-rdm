# Dockerfile that builds a fully functional image of your app.
#
# This image installs all Python dependencies for your application. It's based
# on Almalinux (https://github.com/inveniosoftware/docker-invenio)
# and includes Pip, Pipenv, Node.js, NPM and some few standard libraries
# Invenio usually needs.

FROM registry.cern.ch/inveniosoftware/almalinux:1


RUN dnf install -y epel-release
RUN dnf update -y

# XRootD
ARG xrootd_version="5.5.5"
# Repo required to find all the releases of XRootD
RUN dnf config-manager --add-repo https://cern.ch/xrootd/xrootd.repo
RUN if [ ! -z "$xrootd_version" ] ; then XROOTD_V="-$xrootd_version" ; else XROOTD_V="" ; fi && \
    echo "Will install xrootd version: $XROOTD_V (latest if empty)" && \
    dnf install -y xrootd"$XROOTD_V" python3-xrootd"$XROOTD_V"
# /XRootD

# Kerberos
# CRB (Code Ready Builder): equivalent repository to well-known CentOS PowerTools
RUN dnf install -y yum-utils
RUN dnf config-manager --set-enabled crb
# `krb5-devel` required by requests-kerberos
RUN dnf install -y krb5-workstation krb5-libs krb5-devel
COPY ./krb5.conf /etc/krb5.conf
# /Kerberos

# VIPS
# libvips is not available in EPEL so we install the Remi repository configuration package
# See: https://github.com/libvips/libvips/issues/1184
RUN dnf install -y http://rpms.remirepo.net/enterprise/remi-release-9.rpm
RUN dnf install -y vips
# /VIPS

# Python and uv configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/opt/.cache/uv \
    UV_COMPILE_BYTECODE=1 \
    UV_FROZEN=1 \
    UV_LINK_MODE=copy \
    UV_NO_MANAGED_PYTHON=1 \
    UV_SYSTEM_PYTHON=1 \
    # Tell uv to use system Python
    UV_PROJECT_ENVIRONMENT=/usr/ \
    UV_PYTHON_DOWNLOADS=never \
    UV_REQUIRE_HASHES=1 \
    UV_VERIFY_HASHES=1

# Get latest version of uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install Python dependencies using uv
ARG BUILD_EXTRAS="--extra sentry --extra xrootd"
RUN --mount=type=cache,target=/opt/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-dev --no-install-workspace --no-editable $BUILD_EXTRAS \
        # (py)xrootd is already installed above using dnf
        --no-install-package=xrootd

COPY site ./site
COPY legacy ./legacy

COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./translations ${INVENIO_INSTANCE_PATH}/translations
COPY ./ .

# Make sure workspace packages are installed (zenodo-rdm, zenodo-legacy)
RUN --mount=type=cache,target=/opt/.cache/uv \
    uv sync --frozen --no-dev $BUILD_EXTRAS \
    # (py)xrootd is already installed above using dnf
    --no-install-package=xrootd

# We're caching on a mount, so for any commands that run after this we
# don't want to use the cache (for image filesystem permission reasons)
ENV UV_NO_CACHE=1

# application build args to be exposed as environment variables
ARG IMAGE_BUILD_TIMESTAMP
ARG SENTRY_RELEASE

# Expose random sha to uniquely identify this build
ENV INVENIO_IMAGE_BUILD_TIMESTAMP="'${IMAGE_BUILD_TIMESTAMP}'"
ENV SENTRY_RELEASE=${SENTRY_RELEASE}

RUN echo "Image build timestamp $INVENIO_IMAGE_BUILD_TIMESTAMP"

RUN cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    invenio collect --verbose  && \
    invenio webpack buildall

ENTRYPOINT [ "bash", "-l"]
