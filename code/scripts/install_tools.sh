#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .tools
case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) kind_platform=darwin-arm64; istio_platform=osx-arm64 ;;
  Darwin-x86_64) kind_platform=darwin-amd64; istio_platform=osx-amd64 ;;
  Linux-aarch64|Linux-arm64) kind_platform=linux-arm64; istio_platform=linux-arm64 ;;
  Linux-x86_64) kind_platform=linux-amd64; istio_platform=linux-amd64 ;;
  *) printf 'Unsupported platform\n' >&2; exit 1 ;;
esac
kind_url="https://github.com/kubernetes-sigs/kind/releases/download/v0.33.0/kind-${kind_platform}"
curl -fsSL "$kind_url" -o ".tools/kind-${kind_platform}"
curl -fsSL "${kind_url}.sha256sum" -o ".tools/kind-${kind_platform}.sha256sum"
archive="istio-1.31.1-${istio_platform}.tar.gz"
istio_url="https://github.com/istio/istio/releases/download/1.31.1/${archive}"
curl -fsSL "$istio_url" -o ".tools/${archive}"
curl -fsSL "${istio_url}.sha256" -o ".tools/${archive}.sha256"
pushd .tools >/dev/null
shasum -a 256 -c "kind-${kind_platform}.sha256sum"
expected_digest="$(awk '{print $1}' "${archive}.sha256")"
actual_digest="$(shasum -a 256 "$archive" | awk '{print $1}')"
test "$actual_digest" = "$expected_digest"
printf 'Istio archive SHA256 verified: %s\n' "$actual_digest"
chmod +x "kind-${kind_platform}"
ln -sf "kind-${kind_platform}" kind
tar -xzf "$archive"
popd >/dev/null
.tools/kind version
.tools/istio-1.31.1/bin/istioctl version --remote=false