// docker-bake.hcl
//
// Build all variants in parallel:
//   docker buildx bake
//
// Build specific variant:
//   docker buildx bake almalinux-runtime
//
// Build and push:
//   docker buildx bake --push

variable "REGISTRY" {
  default = "registry.cern.ch/inveniosoftware"
}

variable "VERSION" {
  default = "1"
}

variable "PYTHON_VERSION" {
  default = "3.12"
}

variable "NODE_VERSION" {
  default = "22"
}

// Groups for building multiple targets at once
group "default" {
  targets = ["almalinux-builder", "almalinux-runtime", "almalinux-debug"]
}

group "almalinux" {
  targets = ["almalinux-builder", "almalinux-runtime", "almalinux-debug"]
}

group "debian" {
  targets = ["debian-builder", "debian-runtime", "debian-debug"]
}

group "all" {
  targets = [
    "almalinux-builder", "almalinux-runtime", "almalinux-debug",
    "debian-builder", "debian-runtime", "debian-debug"
  ]
}

// AlmaLinux variants
target "almalinux-builder" {
  dockerfile = "Dockerfile"
  target     = "builder"
  tags       = ["${REGISTRY}/almalinux:${VERSION}-builder"]
  args = {
    PYTHON_VERSION = "${PYTHON_VERSION}"
    NODE_VERSION   = "${NODE_VERSION}"
  }
  cache-from = ["type=registry,ref=${REGISTRY}/almalinux:cache-builder"]
  cache-to   = ["type=registry,ref=${REGISTRY}/almalinux:cache-builder,mode=max"]
}

target "almalinux-runtime" {
  dockerfile = "Dockerfile"
  target     = "runtime"
  tags = [
    "${REGISTRY}/almalinux:${VERSION}-runtime",
    "${REGISTRY}/almalinux:${VERSION}",
    "${REGISTRY}/almalinux:latest"
  ]
  args = {
    PYTHON_VERSION = "${PYTHON_VERSION}"
    NODE_VERSION   = "${NODE_VERSION}"
  }
  cache-from = ["type=registry,ref=${REGISTRY}/almalinux:cache-runtime"]
  cache-to   = ["type=registry,ref=${REGISTRY}/almalinux:cache-runtime,mode=max"]
}

target "almalinux-debug" {
  dockerfile = "Dockerfile"
  target     = "debug"
  tags       = ["${REGISTRY}/almalinux:${VERSION}-debug"]
  args = {
    PYTHON_VERSION = "${PYTHON_VERSION}"
    NODE_VERSION   = "${NODE_VERSION}"
  }
  // Debug builds on top of runtime, so share cache
  cache-from = ["type=registry,ref=${REGISTRY}/almalinux:cache-runtime"]
}

// Debian variants
target "debian-builder" {
  dockerfile = "Dockerfile.debian"
  target     = "builder"
  tags       = ["${REGISTRY}/debian:${VERSION}-builder"]
  args = {
    PYTHON_VERSION = "${PYTHON_VERSION}"
    NODE_VERSION   = "${NODE_VERSION}"
  }
  cache-from = ["type=registry,ref=${REGISTRY}/debian:cache-builder"]
  cache-to   = ["type=registry,ref=${REGISTRY}/debian:cache-builder,mode=max"]
}

target "debian-runtime" {
  dockerfile = "Dockerfile.debian"
  target     = "runtime"
  tags = [
    "${REGISTRY}/debian:${VERSION}-runtime",
    "${REGISTRY}/debian:${VERSION}"
  ]
  args = {
    PYTHON_VERSION = "${PYTHON_VERSION}"
    NODE_VERSION   = "${NODE_VERSION}"
  }
  cache-from = ["type=registry,ref=${REGISTRY}/debian:cache-runtime"]
  cache-to   = ["type=registry,ref=${REGISTRY}/debian:cache-runtime,mode=max"]
}

target "debian-debug" {
  dockerfile = "Dockerfile.debian"
  target     = "debug"
  tags       = ["${REGISTRY}/debian:${VERSION}-debug"]
  args = {
    PYTHON_VERSION = "${PYTHON_VERSION}"
    NODE_VERSION   = "${NODE_VERSION}"
  }
  cache-from = ["type=registry,ref=${REGISTRY}/debian:cache-runtime"]
}

// Multi-platform builds (optional, for ARM support)
target "almalinux-runtime-multiarch" {
  inherits  = ["almalinux-runtime"]
  platforms = ["linux/amd64", "linux/arm64"]
}

target "debian-runtime-multiarch" {
  inherits  = ["debian-runtime"]
  platforms = ["linux/amd64", "linux/arm64"]
}
