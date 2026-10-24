# Cloud & Infrastructure Security — Reference

Scope: the platform *around* the application — IAM, network, storage, secrets stores, IaC,
containers/Kubernetes, CI/CD, and logging. Application-code security (SQLi, XSS, CSRF, authz,
SSRF, deserialization) lives in the main `SKILL.md`; load this file when the work touches
deployment, cloud configuration, or pipelines. Governing principle throughout: **least
privilege plus defense in depth**. Misconfiguration — not exotic exploits — is the leading
cloud breach cause, and OWASP 2025 ranks Security Misconfiguration #2; treat every "it's just
config" change as security-relevant.

## 1. Identity & access management

- **No wildcards in production policies.** Flag `"Action": "*"`, `"Resource": "*"`, `s3:*`,
  `iam:*`. Grant specific actions on specific ARNs, and add `Condition` blocks (source IP,
  MFA-present, tag-match) to privileged policies.
- **No long-lived credentials for workloads.** Workloads assume roles (instance profiles,
  IRSA, workload identity); humans come in through SSO. A static access key in code, IaC, or
  CI is a finding — grep for `AKIA[0-9A-Z]{16}`, `aws_access_key`, `secret_key`.
- **Human access:** the root/owner account is unused day-to-day; MFA on every privileged and
  root account; a documented, alerted break-glass path.
- **Privilege-escalation edges:** deny `iam:PassRole` without a resource constraint; review
  `sts:AssumeRole` chains that widen scope; prune unused credentials on a schedule and run
  periodic access reviews.

```bash
grep -rEn '"\*"|Action.*\*|0\.0\.0\.0/0|AKIA[0-9A-Z]{16}' *.tf *.json *.yaml
```

- [ ] Least-privilege actions + resources, conditions on privileged roles
- [ ] No static keys for workloads; MFA on privileged/root; PassRole constrained
- [ ] Unused credentials pruned; access reviews on a cadence

## 2. Secrets in the cloud and in IaC

- **A managed secrets store, not env-only:** production secrets live in AWS Secrets Manager /
  GCP Secret Manager / Azure Key Vault / Vault and are referenced at runtime. Env vars alone
  are unrotated and unaudited.
- **Terraform state is a secrets store by accident** — DB passwords and tokens land in state
  in plaintext. Remote backend with versioning + KMS encryption + state locking; the state
  bucket private; `terraform.tfstate` gitignored, never committed.
- **No plaintext secrets in IaC source, tfvars, CI YAML, or image layers.** Reference
  secret-store ARNs instead of inlining values. Secret-scan the repo *and its history*
  (trufflehog/gitleaks) in CI.
- **Rotation:** automatic on DB credentials; scheduled for API keys; audit logging enabled on
  secret *reads*, not just writes.

```bash
grep -rEn 'password\s*=|secret\s*=|token\s*=|BEGIN.*PRIVATE KEY|api[_-]?key' *.tf *.tfvars *.yml
```

- [ ] Secrets in a managed store, referenced not inlined; rotation + read-audit on
- [ ] tfstate encrypted, locked, versioned, gitignored; history secret-scanned in CI

## 3. Network security

- **Nothing important open to `0.0.0.0/0`.** Databases, caches, brokers, and admin panels are
  never publicly reachable. Grep IaC for `publicly_accessible = true`, `0.0.0.0/0` on
  non-443 ports, and `from_port 0`/`to_port 65535` ranges.
- **Ingress by least privilege:** app tier accepts only 443 from the load balancer/VPC;
  SSH/RDP only via bastion, VPN, or SSM Session Manager — never open to the internet.
- **Egress matters too:** default-deny where feasible and restrict outbound to what's needed —
  an over-broad egress rule is what turns an SSRF or RCE into data exfiltration.
- **VPC flow logs on**, network ACLs as a second layer under security groups.

- [ ] No public DB/cache/broker; no `0.0.0.0/0` on sensitive ports; bastion/SSM for shell access
- [ ] Egress restricted; flow logs enabled

## 4. Storage and bucket exposure

- **Private by default:** account-level Block Public Access enforced; no ACL or policy
  granting `AllUsers`/`AuthenticatedUsers`/`allUsers`. Grep for `acl = "public-read"` and
  public blob-access settings.
- **Encrypt at rest** (KMS CMK for sensitive data) and require TLS in transit via a policy
  denying insecure transport.
- **Versioning + object lock** on buckets holding audit logs or backups (tamper resistance).
- **Presigned URLs** short-TTL and narrowly scoped — never make a bucket public to share one
  object.

- [ ] Block-public-access on; no public ACL/policy; KMS at rest; TLS-only policy
- [ ] Versioning/object-lock on log and backup buckets

## 5. IaC review and scanning

- **Scan every IaC change in CI** (Checkov, tfsec, KICS, Terrascan) and fail the build on
  high severity.
- **Review the `terraform plan`, not just the apply** — a diff that opens a security group or
  flips `publicly_accessible` must be caught at PR time.
- **Encode least privilege in shared modules** so teams inherit safe defaults instead of
  hand-rolling policies; watch for drift between code and live config.

- [ ] IaC scanner gating CI; plan reviewed in PR; shared least-privilege modules

## 6. Containers and Kubernetes

- **Images:** CVE-scanned in CI (Trivy/Grype); base images pinned by digest; run as non-root
  (`USER`), read-only root filesystem, all capabilities dropped and only needed ones added
  back; no secrets baked into layers.
- **Kubernetes defaults are unsafe — harden explicitly:** RBAC least-privilege (no
  cluster-admin for app service accounts), Pod Security Admission at `restricted`,
  default-deny NetworkPolicies (pods are flat and open by default), no
  `hostNetwork`/`hostPID`/`privileged` pods, etcd encryption at rest (a `Secret` object is
  base64, not encryption), secrets via a CSI secrets-store or sealed-secrets.
- **Workload identity:** pods obtain cloud credentials via IRSA/workload identity, never a
  mounted static key; disable auto-mount of the default service-account token where unused.

- [ ] Non-root, read-only FS, dropped caps, scanned + digest-pinned images
- [ ] RBAC least-privilege, restricted PSA, default-deny NetworkPolicy, etcd encryption
- [ ] Workload identity, not static keys; default SA token auto-mount off where unused

## 7. CI/CD pipeline security

- **OIDC federation, not stored cloud keys:** the pipeline assumes a short-lived role; no
  long-lived `AWS_SECRET_ACCESS_KEY` in CI secrets.
- **Least-privilege job permissions** (`permissions: contents: read`), tokens scoped per job.
- **Pin actions to commit SHAs**, not mutable tags; run secret, dependency, IaC, and
  container-image scans as pipeline gates.
- **Branch protection:** required review, required status checks, signed commits, no direct
  push to `main`; required approvals on the production environment.

- [ ] OIDC not static keys; minimal job permissions; SHA-pinned actions
- [ ] Scan gates in the pipeline; branch protection + prod approvals

## 8. Logging, monitoring, and detection

- **Control-plane audit trail on everywhere** (CloudTrail all regions incl. data events / GCP
  Cloud Audit Logs / Azure Activity Log) and tamper-protected: dedicated account, object
  lock, no delete permissions for operators.
- **Log the security-relevant events:** authN successes/failures, authZ denials, privileged
  actions, secret access, IAM/policy changes, network-rule changes — and never log secrets or
  full PII while doing it.
- **Retention** meets policy (commonly ≥90 days hot, ≥1 year archived); logs centralized and
  append-only.
- **Alert on anomalies** — root-account use, IAM changes, disabled logging, public-bucket or
  security-group changes, authN-failure spikes, new-region activity — wired to a runbook, not
  just a dashboard.
- **Fail closed:** a detection gap (logging disabled, alert pipeline broken) is itself a
  finding — the OWASP A10 "mishandling of exceptional conditions" pattern applied to infra.

- [ ] Audit trail on + tamper-proof; security events logged without secrets
- [ ] Retention met; centralized append-only; anomaly alerts wired to runbooks

## 9. Encryption, backup, and DR

- Encrypt at rest (managed KMS/CMK) and in transit (TLS 1.2+) — enforced by policy, not just
  enabled.
- Automated backups with **tested restores**; point-in-time recovery on databases; deletion
  protection on production stores; defined and *exercised* RPO/RTO.
- Backups encrypted and access-controlled — a readable backup bypasses every live control.

## 10. Pre-deployment cloud checklist

- [ ] IAM least-privilege, no static workload keys, MFA on privileged accounts
- [ ] Secrets in a managed store; tfstate encrypted/locked; no secrets in source or history
- [ ] No public DB/bucket; no `0.0.0.0/0` on sensitive ports; egress restricted
- [ ] IaC scanner gating CI; plans reviewed in PR
- [ ] Images non-root + scanned; K8s RBAC/PSA/NetworkPolicy hardened
- [ ] CI on OIDC with SHA-pinned actions; branch protection + prod approvals
- [ ] Audit logging on and tamper-proof, with anomaly alerts
- [ ] Encryption at rest + transit; tested backups and DR
- [ ] IMDSv2 enforced (hardens the SSRF → metadata path from `SKILL.md`)
- [ ] Compliance obligations (GDPR/HIPAA/PCI as applicable) mapped to controls

## Common misconfigurations — quick scan

Public bucket · `publicly_accessible = true` database · wildcard IAM · long-lived access keys
in CI · plaintext secrets in tfstate/tfvars · security group open on all ports · privileged
or hostNetwork pods · logging disabled or deletable · unencrypted backups · IMDSv1 still
enabled.

Standards worth citing in findings: CIS Benchmarks (AWS/Azure/GCP/Kubernetes), NIST SP
800-190 (containers) and SP 800-53 (AU family for logging), OWASP Top 10 2025, and each
vendor's Well-Architected security pillar.
