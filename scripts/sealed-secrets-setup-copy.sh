#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  MediConnect — Sealed Secrets Setup (FIXED)
#  Run from ANYWHERE in the repo — script resolves paths itself.
#  Usage: bash scripts/sealed-secrets-setup.sh
# ══════════════════════════════════════════════════════════════
set -e

# ── Resolve repo root regardless of where script is called from ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SEALED_DIR="$REPO_ROOT/k8s/sealed-secrets"

echo "📁 Repo root:    $REPO_ROOT"
echo "📁 Sealed dir:   $SEALED_DIR"
echo ""

# ── STEP 1: Verify Sealed Secrets controller is running ───────
echo "🔍 Checking Sealed Secrets controller..."
kubectl get pods -n kube-system | grep sealed-secrets || {
    echo "❌ Sealed Secrets controller not found. Install it first:"
    echo "   kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.26.0/controller.yaml"
    exit 1
}

# ── STEP 2: Create sealed-secrets directory ───────────────────
mkdir -p "$SEALED_DIR"
echo "✅ Created directory: $SEALED_DIR"

# ── STEP 3: Ensure mediconnect namespace exists ───────────────
kubectl apply -f "$REPO_ROOT/k8s/base/namespace.yaml" 2>/dev/null || \
kubectl create namespace mediconnect --dry-run=client -o yaml | kubectl apply -f -

# ── STEP 4: Set your real values here ─────────────────────────
# ⚠️  Fill these in before running. They are only in memory —
#    never written to disk (raw secret files are piped directly
#    into kubeseal without touching the filesystem).

DB_PASSWORD="${DB_PASSWORD:-CHANGE_ME_strong_db_password}"
DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')}"
TWILIO_SID="${TWILIO_SID:-ACxxxxxxxxxxxxxxxxxxxxxxxxx}"
TWILIO_TOKEN="${TWILIO_TOKEN:-xxxxxxxxxxxxxxxxxxxxxxx}"
TWILIO_NUMBER="${TWILIO_NUMBER:-+13464894281}"
SENDGRID_KEY="${SENDGRID_KEY:-SG.xxxxxxxxxxxxxxxxxxxx}"
OPENAI_KEY="${OPENAI_KEY:-sk-proj-xxxxxxxxxxxxxxxxxxx}"
AWS_KEY_ID="${AWS_KEY_ID:-AKIAxxxxxxxxxxxxxxxxxxxxxxx}"
AWS_SECRET="${AWS_SECRET:-xxxxxxxxxxxxxxxxxxxxxxxxxxx}"
INTERNAL_TOKEN="${INTERNAL_TOKEN:-$(python3 -c 'import secrets; print(secrets.token_hex(32))')}"
MONGODB_URI="${MONGODB_URI:-mongodb://mediconnect_user:${DB_PASSWORD}@mongodb-service:27017/mediconnect?authSource=admin}"

echo ""
echo "🔐 Sealing secrets (piping directly through kubeseal)..."

# ── STEP 5: Create and seal each secret ───────────────────────

# 5a. Database credentials
echo "   → db-credentials"
kubectl create secret generic mediconnect-db-credentials \
  --namespace mediconnect \
  --from-literal=POSTGRES_PASSWORD="$DB_PASSWORD" \
  --from-literal=MONGODB_URI="$MONGODB_URI" \
  --from-literal=POSTGRES_EXPORTER_DSN="postgresql://mediconnect_user:${DB_PASSWORD}@postgres-service:5432/mediconnect?sslmode=disable" \
  --dry-run=client -o yaml \
  | kubeseal --format yaml \
  > "$SEALED_DIR/db-credentials-sealed.yaml"
echo "   ✅ $SEALED_DIR/db-credentials-sealed.yaml"

# 5b. Django app secrets
echo "   → app-secrets"
kubectl create secret generic mediconnect-app-secrets \
  --namespace mediconnect \
  --from-literal=SECRET_KEY="$DJANGO_SECRET_KEY" \
  --from-literal=INTERNAL_SERVICE_TOKEN="$INTERNAL_TOKEN" \
  --dry-run=client -o yaml \
  | kubeseal --format yaml \
  > "$SEALED_DIR/app-secrets-sealed.yaml"
echo "   ✅ $SEALED_DIR/app-secrets-sealed.yaml"

# 5c. API keys (Twilio, SendGrid, OpenAI)
echo "   → api-secrets"
kubectl create secret generic mediconnect-api-secrets \
  --namespace mediconnect \
  --from-literal=TWILIO_ACCOUNT_SID="$TWILIO_SID" \
  --from-literal=TWILIO_AUTH_TOKEN="$TWILIO_TOKEN" \
  --from-literal=TWILIO_PHONE_NUMBER="$TWILIO_NUMBER" \
  --from-literal=SENDGRID_API_KEY="$SENDGRID_KEY" \
  --from-literal=OPENAI_API_KEY="$OPENAI_KEY" \
  --dry-run=client -o yaml \
  | kubeseal --format yaml \
  > "$SEALED_DIR/api-secrets-sealed.yaml"
echo "   ✅ $SEALED_DIR/api-secrets-sealed.yaml"

# 5d. AWS credentials
echo "   → aws-secrets"
kubectl create secret generic mediconnect-aws-secrets \
  --namespace mediconnect \
  --from-literal=AWS_ACCESS_KEY_ID="$AWS_KEY_ID" \
  --from-literal=AWS_SECRET_ACCESS_KEY="$AWS_SECRET" \
  --dry-run=client -o yaml \
  | kubeseal --format yaml \
  > "$SEALED_DIR/aws-secrets-sealed.yaml"
echo "   ✅ $SEALED_DIR/aws-secrets-sealed.yaml"

# ── STEP 6: Apply sealed secrets to cluster ───────────────────
echo ""
echo "📦 Applying sealed secrets to cluster..."
kubectl apply -f "$SEALED_DIR/"

# ── STEP 7: Verify secrets were created ──────────────────────
echo ""
echo "🔍 Verifying secrets in mediconnect namespace..."
sleep 3   # Give controller a moment to decrypt and create
kubectl get secrets -n mediconnect

# ── STEP 8: Commit sealed secrets to Git ─────────────────────
echo ""
echo "💾 Committing sealed secrets to Git..."
cd "$REPO_ROOT"
git add k8s/sealed-secrets/
git status k8s/sealed-secrets/

# Only commit if there are staged changes
if git diff --cached --quiet; then
    echo "ℹ️  No new sealed secret changes to commit"
else
    git commit -m "feat: add/update sealed secrets for mediconnect namespace"
    git push
    echo "✅ Sealed secrets committed and pushed"
fi

echo ""
echo "════════════════════════════════════════════════"
echo "  ✅ Sealed Secrets setup complete!"
echo ""
echo "  Files created:"
ls -lh "$SEALED_DIR/"
echo ""
echo "  Auto-generated values (SAVE THESE SOMEWHERE SAFE):"
echo "  Django SECRET_KEY:       ${DJANGO_SECRET_KEY:0:20}..."
echo "  Internal Service Token:  ${INTERNAL_TOKEN:0:16}..."
echo ""
echo "  ⚠️  IMPORTANT: If you recreate the cluster, the Sealed"
echo "     Secrets controller generates a NEW encryption key."
echo "     You must re-run this script after every cluster recreation."
echo "     Keep your real API keys in a password manager."
echo "════════════════════════════════════════════════"

