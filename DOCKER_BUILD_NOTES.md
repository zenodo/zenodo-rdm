# Docker Build Notes

## Overview

This setup provides multi-stage Docker builds for Invenio-based applications:

1. **Base images** (`docker-invenio/`): Generic Invenio builder/runtime/debug images
2. **Application image** (`zenodo-rdm/`): Zenodo-specific production image built on top of base images

## Architecture

All images default to `linux/amd64` platform (required for XRootD which only has x86_64 packages from CERN).

### Base Images (docker-invenio/)

Three variants built from a single Dockerfile:

- **builder**: Full toolchain (gcc, make, node, dev libraries) for compiling Python packages and frontend assets
- **runtime**: Minimal production image with only runtime libraries
- **debug**: Runtime + debugging tools (htop, strace, tcpdump, etc.)

Key features:
- Python 3.14 installed via `uv` (not system packages) for flexibility
- Node.js only in builder (not needed at runtime - assets are pre-built)
- Architecture-specific dnf cache mounts to avoid cross-arch contamination

### Zenodo Image (zenodo-rdm/)

Two-stage build:
1. **Builder stage**: Installs Python deps, builds XRootD bindings, compiles frontend assets
2. **Production stage**: Minimal runtime with venv copied from builder

## Key Decisions & Fixes

### Python 3.14 via uv

Since Python 3.14 isn't in AlmaLinux repos, we use uv's standalone Python builds:

```dockerfile
ENV UV_PYTHON_INSTALL_DIR=/opt/python
RUN uv python install ${PYTHON_VERSION} && \
    ln -sfn $(uv python find ${PYTHON_VERSION}) /usr/local/bin/python
```

### XRootD Python Bindings

The `python3-xrootd` RPM installs to system Python, not the uv-managed venv. Solution:
- Install only C libraries via dnf: `xrootd-client-devel`, `xrootd-client-libs`
- Build Python bindings from PyPI: `uv pip install xrootd==${XROOTD_VERSION}`
- Requires cmake and libuuid-devel for building
- **XRootD 5.9.1+ required for Python 3.14** - older versions fail to build

### BuildKit Cache Mounts

Cache mounts are isolated by architecture to prevent cross-contamination:

```dockerfile
ARG TARGETARCH
RUN --mount=type=cache,target=/var/cache/dnf,sharing=locked,id=dnf-${TARGETARCH} \
    dnf install -y ...
```

**Important**: Don't use `dnf clean all` with cache mounts - the cache isn't part of the image layer anyway, and removal fails because the mount is busy.

### curl vs curl-minimal Conflict

The debug image needs full `curl` but base has `curl-minimal`. Use `--allowerasing`:

```dockerfile
RUN dnf install -y --allowerasing --setopt=install_weak_deps=False curl ...
```

### Invenio Assets Workflow

The `package.json` is generated, not committed. Build sequence:

```dockerfile
# Copy instance assets FIRST (theme.config, custom_fields, etc.)
RUN cp -r ./static/. ${INVENIO_INSTANCE_PATH}/static/ && \
    cp -r ./assets/. ${INVENIO_INSTANCE_PATH}/assets/ && \
    invenio collect --verbose && \
    invenio webpack buildall
```

**Important**: Instance assets (in `./assets/` and `./static/`) must be copied to the instance path BEFORE `invenio collect` and `webpack buildall`. These contain theme overrides like `theme.config` that webpack needs.

### uv sync and XRootD reinstall

When `uv sync` runs to install workspace packages, it may uninstall packages not in `uv.lock` (like xrootd which is installed manually). The Dockerfile reinstalls xrootd after each `uv sync`:

```dockerfile
RUN uv sync --frozen --no-dev ${BUILD_EXTRAS} --no-install-package=xrootd && \
    UV_REQUIRE_HASHES=0 uv pip install --no-cache xrootd==${XROOTD_VERSION}
```

### uv Venv PATH

After `uv sync`, the venv must be in PATH for `invenio` commands:

```dockerfile
ENV PATH="${WORKING_DIR}/src/.venv/bin:${PATH}"
```

### Hash Verification

Zenodo Dockerfile sets `UV_REQUIRE_HASHES=1`. For packages installed outside uv.lock (like xrootd), disable temporarily:

```dockerfile
UV_REQUIRE_HASHES=0 uv pip install --no-cache xrootd==${XROOTD_VERSION}
```

## Build Commands

### Base Images

```bash
cd docker-invenio
make builder    # Build builder image
make runtime    # Build runtime image
make debug      # Build debug image
make all        # Build all variants
```

### Zenodo Image

```bash
cd zenodo-rdm
make build      # Build production image
make build-debug # Build with debug base
```

## Current Issues / TODOs

1. **XRootD build time**: Building xrootd from source takes ~8 minutes due to C++ compilation
2. **pkg_resources deprecation**: Warning about `pkg_resources` in fs package (cosmetic only)

## File Structure

```
docker-invenio/
├── Dockerfile          # AlmaLinux base images
├── Dockerfile.debian   # Debian base images (alternative)
└── Makefile

zenodo-rdm/
├── Dockerfile          # Zenodo production image
└── Makefile
```

## Environment Variables

### Base images set:
- `WORKING_DIR=/opt/invenio`
- `INVENIO_INSTANCE_PATH=/opt/invenio/var/instance`
- `UV_PYTHON=${PYTHON_VERSION}`
- `UV_COMPILE_BYTECODE=1`
- `UV_LINK_MODE=copy`

### Zenodo adds:
- `UV_CACHE_DIR=/opt/.cache/uv`
- `UV_FROZEN=1`
- `UV_REQUIRE_HASHES=1`
- `UV_VERIFY_HASHES=1`
