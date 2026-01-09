# Invenio Base Images - Build Makefile
#
# Usage:
#   make all              # Build all AlmaLinux variants
#   make all-debian       # Build all Debian variants
#   make runtime          # Build only runtime variant
#   make push             # Push all variants to registry

REGISTRY ?= registry.cern.ch/inveniosoftware
VERSION ?= 1
PYTHON_VERSION ?= 3.14
NODE_VERSION ?= 22

# Platform: default to linux/amd64 for consistency with production
# Override with: make PLATFORM=linux/arm64 runtime
PLATFORM ?= linux/amd64

# AlmaLinux variants
ALMA_IMAGE = $(REGISTRY)/almalinux
ALMA_TARGETS = builder runtime debug

# Debian variants
DEBIAN_IMAGE = $(REGISTRY)/debian
DEBIAN_TARGETS = builder runtime debug

.PHONY: all all-debian clean push push-debian help

# Default: build all AlmaLinux variants
all: $(ALMA_TARGETS)

all-debian: $(addprefix debian-,$(DEBIAN_TARGETS))

# AlmaLinux builds
builder:
	docker build \
		--platform $(PLATFORM) \
		--target builder \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--build-arg NODE_VERSION=$(NODE_VERSION) \
		-t $(ALMA_IMAGE):$(VERSION)-builder \
		-f Dockerfile .

runtime:
	docker build \
		--platform $(PLATFORM) \
		--target runtime \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--build-arg NODE_VERSION=$(NODE_VERSION) \
		-t $(ALMA_IMAGE):$(VERSION)-runtime \
		-t $(ALMA_IMAGE):$(VERSION) \
		-f Dockerfile .

debug:
	docker build \
		--platform $(PLATFORM) \
		--target debug \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--build-arg NODE_VERSION=$(NODE_VERSION) \
		-t $(ALMA_IMAGE):$(VERSION)-debug \
		-f Dockerfile .

# Debian builds
debian-builder:
	docker build \
		--platform $(PLATFORM) \
		--target builder \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--build-arg NODE_VERSION=$(NODE_VERSION) \
		-t $(DEBIAN_IMAGE):$(VERSION)-builder \
		-f Dockerfile.debian .

debian-runtime:
	docker build \
		--platform $(PLATFORM) \
		--target runtime \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--build-arg NODE_VERSION=$(NODE_VERSION) \
		-t $(DEBIAN_IMAGE):$(VERSION)-runtime \
		-t $(DEBIAN_IMAGE):$(VERSION) \
		-f Dockerfile.debian .

debian-debug:
	docker build \
		--platform $(PLATFORM) \
		--target debug \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--build-arg NODE_VERSION=$(NODE_VERSION) \
		-t $(DEBIAN_IMAGE):$(VERSION)-debug \
		-f Dockerfile.debian .

# Push to registry
push: all
	docker push $(ALMA_IMAGE):$(VERSION)-builder
	docker push $(ALMA_IMAGE):$(VERSION)-runtime
	docker push $(ALMA_IMAGE):$(VERSION)-debug
	docker push $(ALMA_IMAGE):$(VERSION)

push-debian: all-debian
	docker push $(DEBIAN_IMAGE):$(VERSION)-builder
	docker push $(DEBIAN_IMAGE):$(VERSION)-runtime
	docker push $(DEBIAN_IMAGE):$(VERSION)-debug
	docker push $(DEBIAN_IMAGE):$(VERSION)

# Show image sizes
sizes:
	@echo "=== AlmaLinux variants ==="
	@docker images $(ALMA_IMAGE) --format "table {{.Tag}}\t{{.Size}}"
	@echo ""
	@echo "=== Debian variants ==="
	@docker images $(DEBIAN_IMAGE) --format "table {{.Tag}}\t{{.Size}}"

clean:
	docker rmi $(ALMA_IMAGE):$(VERSION)-builder || true
	docker rmi $(ALMA_IMAGE):$(VERSION)-runtime || true
	docker rmi $(ALMA_IMAGE):$(VERSION)-debug || true
	docker rmi $(ALMA_IMAGE):$(VERSION) || true
	docker rmi $(DEBIAN_IMAGE):$(VERSION)-builder || true
	docker rmi $(DEBIAN_IMAGE):$(VERSION)-runtime || true
	docker rmi $(DEBIAN_IMAGE):$(VERSION)-debug || true
	docker rmi $(DEBIAN_IMAGE):$(VERSION) || true

help:
	@echo "Invenio Base Image Builder"
	@echo ""
	@echo "Targets:"
	@echo "  all           Build all AlmaLinux variants (builder, runtime, debug)"
	@echo "  all-debian    Build all Debian variants"
	@echo "  builder       Build AlmaLinux builder image"
	@echo "  runtime       Build AlmaLinux runtime image"
	@echo "  debug         Build AlmaLinux debug image"
	@echo "  push          Push AlmaLinux images to registry"
	@echo "  push-debian   Push Debian images to registry"
	@echo "  sizes         Show image sizes"
	@echo "  clean         Remove all built images"
	@echo ""
	@echo "Variables:"
	@echo "  REGISTRY=$(REGISTRY)"
	@echo "  VERSION=$(VERSION)"
	@echo "  PLATFORM=$(PLATFORM)"
	@echo "  PYTHON_VERSION=$(PYTHON_VERSION)"
	@echo "  NODE_VERSION=$(NODE_VERSION)"
