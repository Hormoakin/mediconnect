#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  MediConnect — Create & Seal All Production Secrets
#
#  Run this AFTER:
#    1. Cluster is up (kops validate cluster)
#    2. Sealed Secrets controller is installed
#    3. You have all your real API keys ready
#
#  Fill in YOUR real values below before running.
# ══════════════════════════════════════════════════════════════

set -e

# ── YOUR REAL VALUES (fill these in) ──────────────────────────
DB_PASSWORD="YourStrongDatabasePassword123!"
DJANGO_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"

# From console.twilio.com
TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" 
TWILIO_AUTH_TOKEN="e616af73ddcf205b39f35f918d5cda49" 
TWILIO_PHONE_NUMBER="+13464894281"

# From app.sendgrid.com → Settings → API Keys
SENDGRID_KEY="SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# From platform.openai.com → API Keys
OPENAI_KEY="sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# From AWS Console → IAM → Users → Security Credentials
AWS_KEY_ID="AKIAxxxxxxxxxxxxxxxxxxxxxxxx"
AWS_SECRET="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# ── Create namespace first ────────────────────────────────────
kubectl apply -f k8s/base/namespace.yaml

# ── Create & seal each secret ─────────────────────────────────
mkdir -p k8s/sealed-secrets

echo "🔐 Sealing database credentials..."
kubectl create secret generic mediconnect-db-credentials \
  --namespace mediconnect \
  --from-literal=POSTGRES_PASSWORD="${DB_PASSWORD}" \
  --dry-run=client -o yaml \
  | kubeseal --format yaml > k8s/sealed-secrets/db-credentials-sealed.yaml

echo "🔐 Sealing Django app secrets..."
kubectl create secret generic mediconnect-app-secrets \
  --namespace mediconnect \
  --from-literal=SECRET_KEY="${DJANGO_SECRET_KEY}" \
  --dry-run=client -o yaml \
  | kubeseal --format yaml > k8s/sealed-secrets/app-secrets-sealed.yaml

echo "🔐 Sealing API keys (Twilio, SendGrid, OpenAI)..."
kubectl create secret generic mediconnect-api-secrets \
  --namespace mediconnect \
  --from-literal=TWILIO_ACCOUNT_SID="${TWILIO_SID}" \
  --from-literal=TWILIO_AUTH_TOKEN="${TWILIO_TOKEN}" \
  --from-literal=TWILIO_PHONE_NUMBER="${TWILIO_NUMBER}" \
  --from-literal=SENDGRID_API_KEY="${SENDGRID_KEY}" \
  --from-literal=OPENAI_API_KEY="${OPENAI_KEY}" \
  --dry-run=client -o yaml \
  | kubeseal --format yaml > k8s/sealed-secrets/api-secrets-sealed.yaml

echo "🔐 Sealing AWS credentials..."
kubectl create secret generic mediconnect-aws-secrets \
  --namespace mediconnect \
  --from-literal=AWS_ACCESS_KEY_ID="${AWS_KEY_ID}" \
  --from-literal=AWS_SECRET_ACCESS_KEY="${AWS_SECRET}" \
  --dry-run=client -o yaml \
  | kubeseal --format yaml > k8s/sealed-secrets/aws-secrets-sealed.yaml

# ── Apply to cluster ──────────────────────────────────────────
echo ""
echo "📦 Applying sealed secrets to cluster..."
kubectl apply -f k8s/sealed-secrets/

# ── Verify ────────────────────────────────────────────────────
echo ""
echo "✅ Verifying secrets were created..."
kubectl get secrets -n mediconnect

# ── Safe to commit ────────────────────────────────────────────
echo ""
echo "💾 Committing sealed secrets to Git (safe — encrypted)..."
git add k8s/sealed-secrets/
git commit -m "feat: add sealed secrets for mediconnect production namespace"
git push

echo ""
echo "🎉 All secrets sealed and applied!"
echo ""
echo "📋 Auto-generated Django SECRET_KEY (save this somewhere safe):"
echo "   ${DJANGO_SECRET_KEY}"
