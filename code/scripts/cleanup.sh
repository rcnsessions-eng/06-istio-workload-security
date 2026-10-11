#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/cluster_guard.sh
test "${CONFIRM_PRD06_DELETE:-}" = "$cluster_name"
.tools/kind delete cluster --name "$cluster_name" --kubeconfig "$PWD/artifacts/kubeconfig"