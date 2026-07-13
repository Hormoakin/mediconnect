#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  MediConnect — Sealed Secrets Setup Guide
#  Run these commands AFTER the K8s cluster is up and
#  the Sealed Secrets controller is installed.
#
#  Sealed Secrets encrypts your secrets with the cluster's
#  public key. The encrypted YAML files are safe to commit
#  to Git. Only the cluster can decrypt them.
# ══════════════════════════════════════════════════════════════

# ── STEP 1: Verify Sealed Secrets controller is running ───────
kubectl get pods -n kube-system | grep sealed-secrets

# ── STEP 2: Create the raw secrets (NOT committed to Git) ─────

# 2a. Database credentials
kubectl create secret generic mediconnect-db-credentials \
  --namespace mediconnect \
  --from-literal=POSTGRES_PASSWORD='YOUR_STRONG_DB_PASSWORD_HERE' \
  --dry-run=client -o yaml > /tmp/db-credentials-raw.yaml

# 2b. App secrets (Django secret key)
kubectl create secret generic mediconnect-app-secrets \
  --namespace mediconnect \
  --from-literal=SECRET_KEY='YOUR_DJANGO_SECRET_KEY_50_CHARS_MIN' \
  --dry-run=client -o yaml > /tmp/app-secrets-raw.yaml

# 2c. API keys (Twilio, SendGrid, OpenAI)
kubectl create secret generic mediconnect-api-secrets \
  --namespace mediconnect \
  --from-literal=TWILIO_ACCOUNT_SID='ACxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
  --from-literal=TWILIO_AUTH_TOKEN='your-twilio-auth-token' \
  --from-literal=TWILIO_PHONE_NUMBER='+1234567890' \
  --from-literal=SENDGRID_API_KEY='SG.xxxxxxxxxxxxxxxxxxxxxxxx' \
  --from-literal=OPENAI_API_KEY='sk-xxxxxxxxxxxxxxxxxxxxxxxx' \
  --dry-run=client -o yaml > /tmp/api-secrets-raw.yaml

# 2d. AWS credentials
kubectl create secret generic mediconnect-aws-secrets \
  --namespace mediconnect \
  --from-literal=AWS_ACCESS_KEY_ID='AKIAxxxxxxxxxxxxxxxx' \
  --from-literal=AWS_SECRET_ACCESS_KEY='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' \
  --dry-run=client -o yaml > /tmp/aws-secrets-raw.yaml

# ── STEP 3: Seal each secret ──────────────────────────────────

kubeseal --format yaml < /tmp/db-credentials-raw.yaml  > k8s/sealed-secrets/db-credentials-sealed.yaml
kubeseal --format yaml < /tmp/app-secrets-raw.yaml     > k8s/sealed-secrets/app-secrets-sealed.yaml
kubeseal --format yaml < /tmp/api-secrets-raw.yaml     > k8s/sealed-secrets/api-secrets-sealed.yaml
kubeseal --format yaml < /tmp/aws-secrets-raw.yaml     > k8s/sealed-secrets/aws-secrets-sealed.yaml

# ── STEP 4: Clean up raw secret files ────────────────────────
rm /tmp/db-credentials-raw.yaml
rm /tmp/app-secrets-raw.yaml
rm /tmp/api-secrets-raw.yaml
rm /tmp/aws-secrets-raw.yaml

echo "✅ Sealed secrets created in k8s/sealed-secrets/"

# ── STEP 5: Apply sealed secrets to cluster ──────────────────
kubectl apply -f k8s/sealed-secrets/

# ── STEP 6: Verify secrets were created ──────────────────────
kubectl get secrets -n mediconnect

# ── STEP 7: Commit sealed secret files to Git ────────────────
# These are SAFE to commit — they are encrypted
git add k8s/sealed-secrets/
git commit -m "feat: add sealed secrets for mediconnect namespace"
git push

echo ""
echo "⚠️  IMPORTANT: If you recreate the cluster, the Sealed Secrets"
echo "    controller generates a NEW encryption key."
echo "    You must re-seal all secrets after every cluster recreation."
echo "    The raw /tmp/ files have been deleted — keep your real values"
echo "    safe in a password manager (e.g. 1Password / Bitwarden)."
