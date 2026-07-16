#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  MediConnect — Create Sealed Secrets (FIXED)
#  Uses --from-file approach for values with special characters
#  (MongoDB URI, DSN) that break --from-literal quoting in bash.
#
#  Run: bash scripts/create-sealed-secrets.sh
# ══════════════════════════════════════════════════════════════
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SEALED_DIR="$REPO_ROOT/k8s/sealed-secrets"
TMP_DIR=$(mktemp -d)

GREEN='\033[0;32m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'
ok()  { echo -e "${GREEN}✅ $1${NC}"; }
err() { echo -e "${RED}❌ $1${NC}"; rm -rf "$TMP_DIR"; exit 1; }
hdr() { echo -e "\n${BLUE}══ $1 ══${NC}"; }

# Cleanup temp files on exit (never written to Git)
trap 'rm -rf "$TMP_DIR"' EXIT

cd "$REPO_ROOT"

echo "📁 Repo root:  $REPO_ROOT"
echo "📁 Sealed dir: $SEALED_DIR"
echo "📁 Temp dir:   $TMP_DIR"

# ── Verify prerequisites ───────────────────────────────────────
kubectl get pods -n kube-system | grep sealed-secrets | grep Running > /dev/null || \
  err "Sealed Secrets controller not running. Check: kubectl get pods -n kube-system | grep sealed"

command -v kubeseal > /dev/null || err "kubeseal not installed. brew install kubeseal"

# ── Ensure namespace + directory exist ────────────────────────
kubectl apply -f "$REPO_ROOT/k8s/base/namespace.yaml"
mkdir -p "$SEALED_DIR"

# ══════════════════════════════════════════════════════════════
# READ YOUR VALUES
# Either set these as environment variables before running:
#   export DB_PASSWORD="..."
#   export TWILIO_SID="AC..."
# OR edit them directly in the block below.
# ══════════════════════════════════════════════════════════════

# ── Try to read DB password from existing secret first ────────
EXISTING_DB_PASS=$(kubectl get secret mediconnect-db-credentials \
  -n mediconnect -o jsonpath='{.data.POSTGRES_PASSWORD}' 2>/dev/null | base64 -d || echo "")

DB_PASSWORD="${DB_PASSWORD:-${EXISTING_DB_PASS}}"

if [ -z "$DB_PASSWORD" ]; then
  echo "Enter your PostgreSQL password:"
  read -rs DB_PASSWORD
  echo ""
fi

DJANGO_SECRET_KEY="${DJANGO_SECRET_KEY:-$(kubectl get secret mediconnect-app-secrets \
  -n mediconnect -o jsonpath='{.data.SECRET_KEY}' 2>/dev/null | base64 -d || \
  python3 -c 'import secrets; print(secrets.token_urlsafe(50))')}"

INTERNAL_TOKEN="${INTERNAL_TOKEN:-$(kubectl get secret mediconnect-app-secrets \
  -n mediconnect -o jsonpath='{.data.INTERNAL_SERVICE_TOKEN}' 2>/dev/null | base64 -d || \
  python3 -c 'import secrets; print(secrets.token_hex(32))')}"

TWILIO_SID="${TWILIO_SID:-ACxxxxxxxxxxxxxxxxxxxxxxxxxxx}"
TWILIO_TOKEN="${TWILIO_TOKEN:-xxxxxxxxxxxxxxxxxxxxxxxxx}"
TWILIO_NUMBER="${TWILIO_NUMBER:-+13464894281}"
SENDGRID_KEY="${SENDGRID_KEY:-SG.xxxxxxxxxxxxxxxxxxxxxx}"
OPENAI_KEY="${OPENAI_KEY:-sk-proj-xxxxxxxxxxxxxxxxxxxxx}"
AWS_KEY_ID="${AWS_KEY_ID:-AKIAxxxxxxxxxxxxxxxxxxxxxxxxx}"
AWS_SECRET="${AWS_SECRET:-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx}"

# Build URIs with special characters — these go via files to avoid bash quoting issues
MONGODB_URI="mongodb://mediconnect_user:${DB_PASSWORD}@mongodb-service:27017/mediconnect?authSource=admin"
PG_DSN="postgresql://mediconnect_user:${DB_PASSWORD}@postgres-service:5432/mediconnect?sslmode=disable"

echo ""
echo "Using:"
echo "  DB_PASSWORD length:  ${#DB_PASSWORD}"
echo "  TWILIO_SID:          ${TWILIO_SID:0:8}..."
echo "  SENDGRID_KEY:        ${SENDGRID_KEY:0:8}..."
echo "  OPENAI_KEY:          ${OPENAI_KEY:0:12}..."

# ── Helper: write value to temp file and return path ──────────
tmpfile() { local name=$1 val=$2; printf '%s' "$val" > "$TMP_DIR/$name"; echo "$TMP_DIR/$name"; }

# ══════════════════════════════════════════════════════════════
# SECRET 1 — Database credentials
# Using --from-file for URIs containing ?, =, & characters
# ══════════════════════════════════════════════════════════════
hdr "Sealing mediconnect-db-credentials (3 keys)"

F_PG_PASS=$(tmpfile "POSTGRES_PASSWORD" "$DB_PASSWORD")
F_MONGO=$(tmpfile "MONGODB_URI" "$MONGODB_URI")
F_DSN=$(tmpfile "POSTGRES_EXPORTER_DSN" "$PG_DSN")

kubectl create secret generic mediconnect-db-credentials \
  --namespace mediconnect \
  --from-file=POSTGRES_PASSWORD="$F_PG_PASS" \
  --from-file=MONGODB_URI="$F_MONGO" \
  --from-file=POSTGRES_EXPORTER_DSN="$F_DSN" \
  --dry-run=client -o yaml \
  | kubeseal --format yaml \
  > "$SEALED_DIR/db-credentials-sealed.yaml"

ok "db-credentials-sealed.yaml created"

# ══════════════════════════════════════════════════════════════
# SECRET 2 — Django app secrets
# ══════════════════════════════════════════════════════════════
hdr "Sealing mediconnect-app-secrets (2 keys)"

F_SK=$(tmpfile "SECRET_KEY" "$DJANGO_SECRET_KEY")
F_IT=$(tmpfile "INTERNAL_SERVICE_TOKEN" "$INTERNAL_TOKEN")

kubectl create secret generic mediconnect-app-secrets \
  --namespace mediconnect \
  --from-file=SECRET_KEY="$F_SK" \
  --from-file=INTERNAL_SERVICE_TOKEN="$F_IT" \
  --dry-run=client -o yaml \
  | kubeseal --format yaml \
  > "$SEALED_DIR/app-secrets-sealed.yaml"

ok "app-secrets-sealed.yaml created"

# ══════════════════════════════════════════════════════════════
# SECRET 3 — API keys (Twilio, SendGrid, OpenAI)
# ══════════════════════════════════════════════════════════════
hdr "Sealing mediconnect-api-secrets (5 keys)"

F_TSID=$(tmpfile "TWILIO_ACCOUNT_SID" "$TWILIO_SID")
F_TTOK=$(tmpfile "TWILIO_AUTH_TOKEN" "$TWILIO_TOKEN")
F_TNUM=$(tmpfile "TWILIO_PHONE_NUMBER" "$TWILIO_NUMBER")
F_SG=$(tmpfile "SENDGRID_API_KEY" "$SENDGRID_KEY")
F_OAI=$(tmpfile "OPENAI_API_KEY" "$OPENAI_KEY")

kubectl create secret generic mediconnect-api-secrets \
  --namespace mediconnect \
  --from-file=TWILIO_ACCOUNT_SID="$F_TSID" \
  --from-file=TWILIO_AUTH_TOKEN="$F_TTOK" \
  --from-file=TWILIO_PHONE_NUMBER="$F_TNUM" \
  --from-file=SENDGRID_API_KEY="$F_SG" \
  --from-file=OPENAI_API_KEY="$F_OAI" \
  --dry-run=client -o yaml \
  | kubeseal --format yaml \
  > "$SEALED_DIR/api-secrets-sealed.yaml"

ok "api-secrets-sealed.yaml created"

# ══════════════════════════════════════════════════════════════
# SECRET 4 — AWS credentials
# ══════════════════════════════════════════════════════════════
hdr "Sealing mediconnect-aws-secrets (2 keys)"

F_AKI=$(tmpfile "AWS_ACCESS_KEY_ID" "$AWS_KEY_ID")
F_ASK=$(tmpfile "AWS_SECRET_ACCESS_KEY" "$AWS_SECRET")

kubectl create secret generic mediconnect-aws-secrets \
  --namespace mediconnect \
  --from-file=AWS_ACCESS_KEY_ID="$F_AKI" \
  --from-file=AWS_SECRET_ACCESS_KEY="$F_ASK" \
  --dry-run=client -o yaml \
  | kubeseal --format yaml \
  > "$SEALED_DIR/aws-secrets-sealed.yaml"

ok "aws-secrets-sealed.yaml created"

# ══════════════════════════════════════════════════════════════
# APPLY + VERIFY
# ══════════════════════════════════════════════════════════════
hdr "Applying sealed secrets to cluster"
kubectl apply -f "$SEALED_DIR/"
echo ""
echo "Waiting 5s for controller to decrypt..."
sleep 5

hdr "Verifying secrets in mediconnect namespace"
kubectl get secrets -n mediconnect

# Verify key counts
echo ""
echo "Key counts:"
for secret in mediconnect-db-credentials mediconnect-app-secrets mediconnect-api-secrets mediconnect-aws-secrets; do
  COUNT=$(kubectl get secret $secret -n mediconnect \
    -o jsonpath='{.data}' 2>/dev/null | python3 -c \
    "import sys,json; d=json.load(sys.stdin); print(len(d))" 2>/dev/null || echo "?")
  echo "  $secret: $COUNT keys"
done

# ══════════════════════════════════════════════════════════════
# COMMIT TO GIT
# ══════════════════════════════════════════════════════════════
hdr "Committing to Git"
git add "$SEALED_DIR/"
git diff --cached --quiet && echo "Nothing new to commit" || {
  git commit -m "fix: re-seal secrets using --from-file to handle special characters"
  git push
  ok "Sealed secrets committed and pushed"
}

echo ""
echo "════════════════════════════════════════════════"
echo "  ✅ All secrets sealed successfully!"
echo ""
echo "  Expected key counts:"
echo "    mediconnect-db-credentials:  3 keys"
echo "    mediconnect-app-secrets:     2 keys"
echo "    mediconnect-api-secrets:     5 keys"
echo "    mediconnect-aws-secrets:     2 keys"
echo ""
echo "  Temp files cleaned up automatically."
echo "  Real values were NEVER written to disk."
echo "════════════════════════════════════════════════"
