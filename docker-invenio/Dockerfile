# syntax=docker/dockerfile:1
#
# Invenio Base Docker Images
#
# Build targets:
#   docker build --target builder -t inveniosoftware/almalinux:1-builder .
#   docker build --target runtime -t inveniosoftware/almalinux:1-runtime .
#   docker build --target debug   -t inveniosoftware/almalinux:1-debug .
#
# Copyright (C) 2018-2025 CERN.
# Copyright (C) 2022      Graz University of Technology.
# Copyright (C) 2022      University of Münster.
# Copyright (C) 2023-2024 KTH Royal Institute of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

ARG LINUX_VERSION=9
ARG PYTHON_VERSION=3.14
ARG NODE_VERSION=22

# =============================================================================
# BASE: Common configuration shared by all variants
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

# Create invenio user (UID 1000 for compatibility with common setups)
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

# Install Python via uv (standalone builds, works for any version)
ENV UV_PYTHON_INSTALL_DIR=/opt/python
RUN uv python install ${PYTHON_VERSION} && \
    ln -sfn $(uv python find ${PYTHON_VERSION}) /usr/local/bin/python && \
    ln -sfn $(uv python find ${PYTHON_VERSION}) /usr/local/bin/python3

# uv configuration
ENV UV_PYTHON=${PYTHON_VERSION} \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# =============================================================================
# RUNTIME: Minimal production image with only runtime dependencies
# =============================================================================
FROM base AS runtime

ARG TARGETARCH

# Enable EPEL and CRB for additional packages
RUN dnf install -y dnf-plugins-core && \
    dnf config-manager --set-enabled crb && \
    dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm && \
    dnf clean all

# Install runtime-only system libraries
# Note: These are the RUNTIME packages (no -devel suffix)
RUN --mount=type=cache,target=/var/cache/dnf,sharing=locked,id=dnf-${TARGETARCH} \
    dnf install -y --setopt=install_weak_deps=False \
        # Runtime libraries (shared objects only, no headers)
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
        # Fonts for PDF/image generation
        dejavu-sans-fonts \
        # Git (often needed at runtime for editable installs)
        git

# Labels
LABEL org.opencontainers.image.title="Invenio Base (Runtime)" \
      org.opencontainers.image.description="Minimal runtime image for Invenio applications" \
      org.opencontainers.image.vendor="Invenio Software" \
      org.opencontainers.image.licenses="MIT"

# =============================================================================
# BUILDER: Full toolchain for compiling Python/Node.js packages
# =============================================================================
FROM base AS builder

ARG NODE_VERSION
ARG TARGETARCH

# Enable EPEL and CRB
RUN dnf install -y dnf-plugins-core && \
    dnf config-manager --set-enabled crb && \
    dnf install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm && \
    dnf clean all

# Install build tools and development libraries
RUN --mount=type=cache,target=/var/cache/dnf,sharing=locked,id=dnf-${TARGETARCH} \
    dnf install -y --setopt=install_weak_deps=False \
        # Build essentials
        gcc \
        gcc-c++ \
        make \
        pkgconf \
        # Development libraries (headers + static libs for compilation)
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
        # Other build dependencies
        git \
        # Fonts
        dejavu-sans-fonts

# Install Node.js with npm for asset building
RUN curl -fsSL https://rpm.nodesource.com/setup_${NODE_VERSION}.x | bash - && \
    dnf install -y --setopt=install_weak_deps=False nodejs && \
    dnf clean all && \
    rm -rf /var/cache/dnf && \
    corepack enable

# Labels
LABEL org.opencontainers.image.title="Invenio Base (Builder)" \
      org.opencontainers.image.description="Full toolchain for building Invenio applications" \
      org.opencontainers.image.vendor="Invenio Software" \
      org.opencontainers.image.licenses="MIT"

# =============================================================================
# DEBUG: Runtime + debugging/inspection tools
# =============================================================================
FROM runtime AS debug

ARG TARGETARCH

# Install debugging and inspection tools
RUN --mount=type=cache,target=/var/cache/dnf,sharing=locked,id=dnf-${TARGETARCH} \
    dnf install -y --allowerasing --setopt=install_weak_deps=False \
        # Process inspection
        procps-ng \
        htop \
        strace \
        lsof \
        # File inspection
        file \
        less \
        vim-minimal \
        # Disk/IO monitoring
        iotop \
        iftop \
        # Network debugging
        tcpdump \
        bind-utils \
        net-tools \
        curl \
        wget

LABEL org.opencontainers.image.title="Invenio Base (Debug)" \
      org.opencontainers.image.description="Runtime image with debugging tools for troubleshooting" \
      org.opencontainers.image.vendor="Invenio Software" \
      org.opencontainers.image.licenses="MIT"
