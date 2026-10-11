FROM zero-trust-identity-delegation-checks:0.1.0 AS checks
COPY 06-istio-workload-security/code/scripts /mesh-scripts
COPY 06-istio-workload-security/code/pyproject.toml /mesh/pyproject.toml
CMD ["sh", "-c", "ruff check --config /mesh/pyproject.toml /mesh-scripts && ruff format --check --config /mesh/pyproject.toml /mesh-scripts && mypy --config-file /mesh/pyproject.toml /mesh-scripts"]