# Day 13 lab: deploy an AI service to the cloud, safely

Steps 1-3 need nothing but Python. Steps 4-7 need a Google Cloud project (the free trial is enough);
the same ideas map one-to-one to AWS (ECR, App Runner/ECS, RDS) and Azure (ACR, Container Apps, Azure Database).

## Step 1: the smoke test
```bash
python day13_cloud/smoke_test.py --selftest
```
Deploy A passes. Deploy B is the classic silent failure: the old container is still running and the secret is missing,
yet `/health` says ok. Health checks prove the process is alive, not that the RIGHT thing is live.

## Step 2: the canary rule
```bash
python day13_cloud/canary.py
```
Four outcomes: wait (too little traffic to judge), promote, roll back for latency, roll back for quality.
Change `RULES` and see which cases flip. Write your rule down before a rollout, not after.

## Step 3: read the deploy files
- `cloudrun/deploy.yml`: CI builds one image tagged with the commit, deploys it with **no traffic**, smoke tests the
  canary URL, then sends 10% of traffic. No JSON key is stored in GitHub: it uses Workload Identity Federation.
- `cloudrun/service.yaml`: the same service written declaratively (min/max instances, concurrency, secrets, probes).
- `vm/deploy_vm.sh`: the single-VM version: keep the old container renamed, start a new one, smoke test, auto-rollback.
- `vm/nginx_tls.conf`: HTTPS with Let's Encrypt in front of a container that only listens on localhost.

## Step 4: one-time cloud setup (GCP)
```bash
gcloud config set project MY_PROJECT
gcloud services enable run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com
gcloud artifacts repositories create apps --repository-format=docker --location=asia-south1
printf 'my-real-key' | gcloud secrets create api-key --data-file=-
gcloud iam service-accounts create model-service
gcloud secrets add-iam-policy-binding api-key \
  --member=serviceAccount:model-service@MY_PROJECT.iam.gserviceaccount.com --role=roles/secretmanager.secretAccessor
```
The runtime service account can read ONE secret and nothing else: least privilege.

## Step 5: deploy by hand once
```bash
IMAGE=asia-south1-docker.pkg.dev/MY_PROJECT/apps/model-service
TAG=main-$(git rev-parse --short HEAD)
gcloud auth configure-docker asia-south1-docker.pkg.dev
docker build -f day11_git_docker/docker/Dockerfile -t $IMAGE:$TAG . && docker push $IMAGE:$TAG
gcloud run deploy model-service --image $IMAGE:$TAG --region asia-south1 \
  --service-account model-service@MY_PROJECT.iam.gserviceaccount.com \
  --set-env-vars APP_VERSION=$TAG --set-secrets API_KEY=api-key:latest --allow-unauthenticated
python day13_cloud/smoke_test.py https://model-service-xxxx.a.run.app --version $TAG
```

## Step 6: rotate the secret and prove it is live
```bash
printf 'new-key' | gcloud secrets versions add api-key --data-file=-
gcloud run deploy model-service --image $IMAGE:$TAG --region asia-south1 --set-secrets API_KEY=api-key:latest
```
A running instance does not pick up a new secret version by itself: a new revision does. Same lesson as Day 11's
`docker restart` trap. Then verify (the smoke test, or `/config`).

## Step 7: roll back
```bash
gcloud run revisions list --service model-service --region asia-south1
gcloud run services update-traffic model-service --region asia-south1 --to-revisions model-service-00001-abc=100
```
Seconds, no rebuild: the old revision's image is still in the registry.

## Databases: backups are not a plan until you have restored one
Managed Postgres (Cloud SQL, RDS) gives you daily backups and, if you turn it on, point-in-time recovery (PITR):
restore to any second in the retention window, e.g. just before a bad migration.
```bash
gcloud sql instances patch my-db --backup-start-time=02:00 --enable-point-in-time-recovery
gcloud sql instances clone my-db my-db-restore-test --point-in-time=2026-11-10T04:00:00Z   # practise a restore
```
Know three numbers for every database: how often it is backed up, how far back you can go, and how long a restore takes.

## Clean up
`gcloud run services delete model-service --region asia-south1` and delete any test database clones (they cost money).
