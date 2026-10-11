#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/cluster_guard.sh
kubectl --kubeconfig "$PWD/artifacts/kubeconfig" scale deployment/gateway -n learning-mesh --replicas=0
printf 'Gateway stopped; strict mTLS and caller restrictions retained. Redeploy manifests to restore.\n'