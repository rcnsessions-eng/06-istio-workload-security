#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash -n scripts/install_tools.sh scripts/create_cluster.sh scripts/deploy.sh scripts/check.sh scripts/rollback.sh scripts/cleanup.sh
docker compose config --quiet
docker compose build checks
docker compose run --rm checks
source scripts/cluster_guard.sh
kubectl --kubeconfig "$PWD/artifacts/kubeconfig" apply --dry-run=server -f deploy/kubernetes/workloads.yaml
kubectl --kubeconfig "$PWD/artifacts/kubeconfig" apply --dry-run=server -f deploy/istio/security.yaml
.tools/istio-1.31.1/bin/istioctl --kubeconfig "$PWD/artifacts/kubeconfig" validate -f deploy/istio/security.yaml
.tools/istio-1.31.1/bin/istioctl --kubeconfig "$PWD/artifacts/kubeconfig" analyze -n learning-mesh
python3 scripts/verify.py