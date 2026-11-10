# Day 13: Cloud deployment for AI services

From a container on your laptop to a service on the internet: registry, Cloud Run or a VM, secrets,
HTTPS, canary releases, smoke tests, rollback and database backups.

| File | What it is |
|---|---|
| [smoke_test.py](smoke_test.py) | Post-deploy checks against a real URL: health, the right version, secret present, a known model answer, clean errors. Exit code drives rollback |
| [canary.py](canary.py) | The promote / wait / roll back rule for a canary, written down before the rollout |
| [cloudrun/deploy.yml](cloudrun/deploy.yml) | GitHub Actions: build once, push to Artifact Registry, deploy with no traffic, smoke test, 10% canary. Keyless auth |
| [cloudrun/service.yaml](cloudrun/service.yaml) | The Cloud Run service as a reviewed file: scaling, concurrency, secrets from Secret Manager, probes |
| [vm/deploy_vm.sh](vm/deploy_vm.sh) | Single-VM container swap: keep the old one, start the new one, smoke test, automatic rollback |
| [vm/nginx_tls.conf](vm/nginx_tls.conf) | Nginx + Let's Encrypt HTTPS in front of a localhost-only container, with streaming settings |
| [LAB.md](LAB.md) | Seven steps, from the offline self-tests to a real deploy, secret rotation, rollback and a restore drill |
| [INTERVIEW_QA.md](INTERVIEW_QA.md) | Interview questions with full explanations and spoken answers |

## Quick start
```bash
python day13_cloud/smoke_test.py --selftest
python day13_cloud/canary.py
```

## Five lessons from a real production AI platform
1. Health checks prove the process is alive, not that the right version is live. Check the version after every deploy.
2. A secret change needs a new container or revision, then verification. A restart may reuse the old value.
3. Keep the previous version ready. A one-command rollback turns an outage into a blip.
4. Build once, tag by commit, deploy the same image everywhere. Rebuilding for prod ships untested code.
5. Backups you have never restored are a hope, not a plan. Know your backup frequency, PITR window and restore time.
