# Dockerfile that builds a fully functional image of your app.
#
# This image installs all Python dependencies for your application. It's based
# on Almalinux (https://github.com/inveniosoftware/docker-invenio)
# and includes Pip, Pipenv, Node.js, NPM and some few standard libraries
# Invenio usually needs.
#
# Note: It is important to keep the commands in this file in sync with your
# bootstrap script located in ./scripts/bootstrap.

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
# Install libvips (pinned to 8.15.2 because of a conversion bug)
RUN dnf install -y vips-8.15.2-1.el9.remi
# /VIPS

# XRootD
RUN pip install "requests-kerberos==0.14.0"
RUN pip install "invenio-xrootd==2.0.0a2"
# /XRootD

COPY site ./site
COPY legacy ./legacy
COPY Pipfile Pipfile.lock ./
RUN pipenv install --deploy --system

COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}
COPY ./invenio.cfg ${INVENIO_INSTANCE_PATH}
COPY ./templates/ ${INVENIO_INSTANCE_PATH}/templates/
COPY ./app_data/ ${INVENIO_INSTANCE_PATH}/app_data/
COPY ./translations ${INVENIO_INSTANCE_PATH}/translations
COPY ./ .

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
