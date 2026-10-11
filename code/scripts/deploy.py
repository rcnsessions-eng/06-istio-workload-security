import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSHOPS = ROOT.parents[1]
KUBECONFIG = ROOT / "artifacts/kubeconfig"


def kubectl(*args: str, payload: str | None = None) -> None:
    subprocess.run(
        ["kubectl", "--kubeconfig", str(KUBECONFIG), *args],
        input=payload,
        text=True,
        check=True,
    )


def main() -> None:
    context = subprocess.check_output(
        ["kubectl", "--kubeconfig", str(KUBECONFIG), "config", "current-context"],
        text=True,
    ).strip()
    if context not in {"kind-zero-trust-workload-security", "kind-zero-trust-prd06"}:
        raise RuntimeError("Only the dedicated local PRD 06 cluster is permitted")
    kubectl("apply", "-f", str(ROOT / "deploy/kubernetes/namespaces.yaml"))
    settings = json.loads(
        subprocess.check_output(
            ["docker", "compose", "--profile", "tools", "config", "--format", "json"],
            cwd=WORKSHOPS / "05-identity-delegation/code",
            text=True,
        )
    )["services"]["smoke"]["environment"]
    for namespace in ["learning-mesh", "learning-identity-fixtures"]:
        kubectl(
            "apply",
            "--server-side",
            "-f",
            "-",
            payload=json.dumps(
                {
                    "apiVersion": "v1",
                    "kind": "Secret",
                    "metadata": {"name": "identity-fixtures", "namespace": namespace},
                    "type": "Opaque",
                    "stringData": {
                        name: settings[name]
                        for name in ["LEARNING_DEMO_PASSWORD", "LEARNING_AGENT_SECRET"]
                    },
                }
            ),
        )
    kubectl(
        "apply",
        "--server-side",
        "-f",
        "-",
        payload=json.dumps(
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {
                    "name": "learning-realm",
                    "namespace": "learning-identity-fixtures",
                },
                "data": {
                    "learning-realm.json": (
                        WORKSHOPS / "05-identity-delegation/code/keycloak/learning-realm.json"
                    ).read_text()
                },
            }
        ),
    )
    policy_data = {}
    for relative in [
        "02-opa-authorization/code/policy/rego",
        "04-mcp-constrained-tools/code/policy/rego",
    ]:
        for policy in (WORKSHOPS / relative).glob("*.rego"):
            policy_data[policy.name] = policy.read_text()
    kubectl(
        "apply",
        "--server-side",
        "-f",
        "-",
        payload=json.dumps(
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {"name": "learning-policies", "namespace": "learning-mesh"},
                "data": policy_data,
            }
        ),
    )
    kubectl("apply", "-f", str(ROOT / "deploy/istio/security.yaml"))
    kubectl("apply", "-f", str(ROOT / "deploy/kubernetes/workloads.yaml"))
    kubectl(
        "rollout",
        "status",
        "deployment/keycloak",
        "-n",
        "learning-identity-fixtures",
        "--timeout=180s",
    )
    kubectl("rollout", "status", "deployment/gateway", "-n", "learning-mesh", "--timeout=180s")
    kubectl("rollout", "status", "deployment/opa", "-n", "learning-mesh", "--timeout=180s")
    kubectl(
        "wait",
        "--for=condition=Ready",
        "pod/approved-mcp",
        "pod/unapproved-client",
        "pod/plaintext-client",
        "-n",
        "learning-mesh",
        "--timeout=180s",
    )


if __name__ == "__main__":
    main()
