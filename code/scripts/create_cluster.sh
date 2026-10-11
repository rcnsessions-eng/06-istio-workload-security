#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p artifacts
original_context="$(kubectl config current-context)"
if [[ -f artifacts/kubeconfig ]]; then
  source scripts/cluster_guard.sh
  printf 'Retaining existing dedicated cluster: %s\n' "$cluster_name"
elif .tools/kind get clusters | grep -qx zero-trust-workload-security; then
  printf 'Dedicated cluster already exists; retaining it\n'
  .tools/kind export kubeconfig --name zero-trust-workload-security --kubeconfig "$PWD/artifacts/kubeconfig"
else
  .tools/kind create cluster --name zero-trust-workload-security --config deploy/kind.yaml \
    --kubeconfig "$PWD/artifacts/kubeconfig" --wait 180s
fi
test "$(kubectl config current-context)" = "$original_context"
source scripts/cluster_guard.sh
.tools/istio-1.31.1/bin/istioctl --kubeconfig "$PWD/artifacts/kubeconfig" \
  install -f deploy/istio/install.yaml -y
kubectl --kubeconfig "$PWD/artifacts/kubeconfig" get nodes