# Release Notes

## v1.2 — May 2026

### Security Hardening: exec() Blast Radius Minimization

The Custom Converter Service uses `exec()` to run customer-written Python converters. This release adds three defense-in-depth layers that minimize what converter code can do, even if it passes the human review/approval process:

**Layer B — Zero-Permission AWS Session**
- Before `exec()`, the Lambda assumes a temporary IAM role with an explicit deny-all session policy
- Converter code cannot use `import boto3` to access any AWS service
- Original credentials restored after execution completes

**Layer C — Network Isolation (VPC)**
- Custom Converter Lambda runs in a VPC with private isolated subnets and no NAT gateway
- Converter code cannot reach the internet — blocks data exfiltration and payload download
- VPC endpoints for S3, DynamoDB, and STS allow the wrapper code to function normally

**Layer D — Scrubbed Execution Namespace**
- `os.environ` cleared before `exec()` — converter code cannot read secrets or config
- Dangerous builtins removed: `open`, `exec`, `eval`, `compile`, `__import__`
- Environment restored in `finally` block after execution

### Infrastructure: Dynamic Lambda Layers

- Removed vendored third-party Python packages from repository (5,128 files, 76MB)
- Lambda layers now built dynamically at deploy time using `PythonLayerVersion` CDK construct
- Package versions pinned in `requirements.txt` files for deterministic builds
- **New prerequisite**: Docker required on build machine for `cdk deploy`

### Security Scanner Compliance

- ProbeScan: 0 critical findings (down from 192 in initial scan)
- Holmes: 2 medium findings (exec() — mitigated by Layers B+C+D above)
- Added `.gitleaks.toml`, `.semgrepignore`, `.bandit`, `pyproject.toml` scanner configs
- Repository size reduced from ~27MB to ~1MB

---

## v1.1 — May 2026

### Security Scanner Remediation

- Added `.flush()` to tempfile usage in DVaaS and Multi-Instrument Lambdas
- Updated npm dependencies (rollup, lodash, postcss) to patch known CVEs
- Removed `dashboard/cdk.out/` build artifacts and `dashboard/proxy.py` dev tool from repository
- Added `# nosec` annotations to 20 vendored library lines flagged by bandit

### Customer Delivery

- Tarball delivered with SHA-256 integrity verification
- No application logic changes from v1.0

---

## v1.0 — April 2026

### Initial Release

- Multi-instrument ASM conversion (31+ instruments via allotropy library)
- AI-powered conversion fallback (AWS Bedrock Claude 3.5 Sonnet)
- ASM validation against official Allotrope JSON schemas (jsonschema-rs)
- Pluggable validation framework with JSON rule engine
- Custom converter registration with human approval workflow
- Self-contained JWT authentication (no external identity provider required)
- React dashboard (AWS Cloudscape) with 7 tabs + Tools menu
- Full CDK infrastructure-as-code deployment
- Air-gapped deployment support (pre-built Lambda layers)
- Apache 2.0 license
