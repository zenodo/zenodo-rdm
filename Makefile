# Zenodo Docker Image Build
#
# Usage:
#   make build            # Build production image
#   make build-no-cache   # Build without cache
#   make push             # Push to registry

REGISTRY ?= registry.cern.ch/zenodo
IMAGE_NAME ?= zenodo-rdm
VERSION ?= $(shell git rev-parse --short HEAD)
FULL_VERSION ?= $(shell git describe --tags --always)

# Build timestamp for tracking
BUILD_TIMESTAMP := $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")

# Invenio base image settings
INVENIO_REGISTRY ?= registry.cern.ch/inveniosoftware
INVENIO_BASE_VERSION ?= 1

# XRootD version (5.9.1+ required for Python 3.14)
XROOTD_VERSION ?= 5.9.1

# Platform: XRootD only available for amd64
PLATFORM ?= linux/amd64

.PHONY: build build-no-cache push run shell test clean help

build:
	docker build \
		--platform $(PLATFORM) \
		--build-arg INVENIO_BASE_VERSION=$(INVENIO_BASE_VERSION) \
		--build-arg REGISTRY=$(INVENIO_REGISTRY) \
		--build-arg XROOTD_VERSION=$(XROOTD_VERSION) \
		--build-arg IMAGE_BUILD_TIMESTAMP="$(BUILD_TIMESTAMP)" \
		--build-arg SENTRY_RELEASE="$(FULL_VERSION)" \
		-t $(REGISTRY)/$(IMAGE_NAME):$(VERSION) \
		-t $(REGISTRY)/$(IMAGE_NAME):latest \
		.

build-no-cache:
	docker build --no-cache \
		--platform $(PLATFORM) \
		--build-arg INVENIO_BASE_VERSION=$(INVENIO_BASE_VERSION) \
		--build-arg REGISTRY=$(INVENIO_REGISTRY) \
		--build-arg XROOTD_VERSION=$(XROOTD_VERSION) \
		--build-arg IMAGE_BUILD_TIMESTAMP="$(BUILD_TIMESTAMP)" \
		--build-arg SENTRY_RELEASE="$(FULL_VERSION)" \
		-t $(REGISTRY)/$(IMAGE_NAME):$(VERSION) \
		-t $(REGISTRY)/$(IMAGE_NAME):latest \
		.

# Build using the debug base image (for troubleshooting)
build-debug:
	docker build \
		--platform $(PLATFORM) \
		--build-arg INVENIO_BASE_VERSION=$(INVENIO_BASE_VERSION)-debug \
		--build-arg REGISTRY=$(INVENIO_REGISTRY) \
		--build-arg XROOTD_VERSION=$(XROOTD_VERSION) \
		--build-arg IMAGE_BUILD_TIMESTAMP="$(BUILD_TIMESTAMP)" \
		--build-arg SENTRY_RELEASE="$(FULL_VERSION)" \
		-t $(REGISTRY)/$(IMAGE_NAME):$(VERSION)-debug \
		.

push:
	docker push $(REGISTRY)/$(IMAGE_NAME):$(VERSION)
	docker push $(REGISTRY)/$(IMAGE_NAME):latest

# Local development helpers
run:
	docker run -it --rm \
		-p 5000:5000 \
		-v $(PWD)/invenio.cfg:/opt/invenio/var/instance/invenio.cfg:ro \
		$(REGISTRY)/$(IMAGE_NAME):latest

shell:
	docker run -it --rm \
		-v $(PWD):/opt/invenio/src \
		$(REGISTRY)/$(IMAGE_NAME):latest \
		bash

# Show final image size and layers
inspect:
	@echo "=== Image Size ==="
	@docker images $(REGISTRY)/$(IMAGE_NAME):$(VERSION) --format "{{.Size}}"
	@echo ""
	@echo "=== Layer History ==="
	@docker history $(REGISTRY)/$(IMAGE_NAME):$(VERSION)

# Security scan with trivy
scan:
	trivy image $(REGISTRY)/$(IMAGE_NAME):$(VERSION)

clean:
	docker rmi $(REGISTRY)/$(IMAGE_NAME):$(VERSION) || true
	docker rmi $(REGISTRY)/$(IMAGE_NAME):latest || true
	docker rmi $(REGISTRY)/$(IMAGE_NAME):$(VERSION)-debug || true

help:
	@echo "Zenodo Docker Build"
	@echo ""
	@echo "Targets:"
	@echo "  build          Build production image"
	@echo "  build-no-cache Build without Docker cache"
	@echo "  build-debug    Build with debug base (includes htop, strace, etc.)"
	@echo "  push           Push to registry"
	@echo "  run            Run container locally"
	@echo "  shell          Open shell in container"
	@echo "  inspect        Show image size and layers"
	@echo "  scan           Security scan with trivy"
	@echo "  clean          Remove built images"
	@echo ""
	@echo "Current settings:"
	@echo "  VERSION=$(VERSION)"
	@echo "  FULL_VERSION=$(FULL_VERSION)"
	@echo "  INVENIO_BASE_VERSION=$(INVENIO_BASE_VERSION)"
	@echo "  XROOTD_VERSION=$(XROOTD_VERSION)"
