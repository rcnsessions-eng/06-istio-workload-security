#!/usr/bin/env bash
cluster_context="$(kubectl --kubeconfig "$PWD/artifacts/kubeconfig" config current-context)"
case "$cluster_context" in
  kind-zero-trust-workload-security) cluster_name=zero-trust-workload-security ;;
  kind-zero-trust-prd06) cluster_name=zero-trust-prd06 ;;
  *) printf 'Refusing a cluster outside this workshop\n' >&2; exit 1 ;;
esac
.tools/kind get clusters | grep -qx "$cluster_name"