#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/cluster_guard.sh
.tools/kind load docker-image zero-trust-identity-delegation-gateway:0.1.0 --name "$cluster_name"
python3 scripts/deploy.py
.tools/istio-1.31.1/bin/istioctl --kubeconfig "$PWD/artifacts/kubeconfig" validate \
  -f deploy/istio/security.yaml
.tools/istio-1.31.1/bin/istioctl --kubeconfig "$PWD/artifacts/kubeconfig" analyze -n learning-mesh