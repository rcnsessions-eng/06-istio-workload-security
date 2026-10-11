import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KUBECONFIG = ROOT / "artifacts/kubeconfig"


def kubectl(*args: str, source: str | None = None) -> str:
    return subprocess.check_output(
        ["kubectl", "--kubeconfig", str(KUBECONFIG), *args],
        input=source,
        text=True,
    )


def probe(pod: str, source: str) -> None:
    print(
        kubectl(
            "exec",
            "-i",
            pod,
            "-n",
            "learning-mesh",
            "-c",
            "client",
            "--",
            "python",
            "-",
            source=source,
        ).strip()
    )


def main() -> None:
    assert kubectl("config", "current-context").strip() in {
        "kind-zero-trust-workload-security",
        "kind-zero-trust-prd06",
    }
    pods = json.loads(kubectl("get", "pods", "-n", "learning-mesh", "-o", "json"))["items"]
    for pod in pods:
        names = {
            container["name"]
            for container in (pod["spec"]["containers"] + pod["spec"].get("initContainers", []))
        }
        if pod["metadata"]["name"] == "plaintext-client":
            assert "istio-proxy" not in names
        else:
            assert "istio-proxy" in names
    probe(
        "approved-mcp",
        """
import httpx
with httpx.Client(trust_env=False, timeout=3) as client:
    response=client.get("http://gateway:8000/health")
    assert response.status_code == 200
    missing=client.get("http://gateway:8000/v1/delegated/context")
    assert missing.status_code == 401
    certificate=client.get("http://127.0.0.1:15000/certs").text
    assert "spiffe://learning.local/ns/learning-mesh/sa/learning-mcp" in certificate
    denied=client.post("http://opa:8181/v1/data/learning/authz/decision", json={"input":{}})
    assert denied.status_code == 403
print("Approved mTLS caller: health 200, missing user 401, "
    "declared SPIFFE identity, direct OPA denied")
""",
    )
    probe(
        "unapproved-client",
        """
import httpx
with httpx.Client(trust_env=False, timeout=3) as client:
    response=client.get("http://gateway:8000/health")
    assert response.status_code == 403
    assert "RBAC" in response.text
    certificate=client.get("http://127.0.0.1:15000/certs").text
    assert "spiffe://learning.local/ns/learning-mesh/sa/unapproved-client" in certificate
print("Enrolled wrong service account: mesh RBAC denied 403")
""",
    )
    probe(
        "plaintext-client",
        """
import httpx
with httpx.Client(trust_env=False, timeout=3) as client:
    try:
        response=client.get("http://gateway:8000/health")
    except httpx.TransportError:
        pass
    else:
        raise AssertionError("Plaintext path accepted: " + str(response.status_code))
print("Unenrolled plaintext caller: transport rejected before HTTP")
""",
    )
    smoke = kubectl(
        "exec",
        "approved-mcp",
        "-n",
        "learning-mesh",
        "-c",
        "client",
        "--",
        "python",
        "/identity-scripts/smoke.py",
    )
    print(smoke.strip())
    assert "duplicate writes passed" in smoke
    print("PRD 06 live mesh security checks passed")


if __name__ == "__main__":
    main()
