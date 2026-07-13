#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  MediConnect — Patch Missing Secret Keys + Full Backend Deploy
#  Run from repo root: bash scripts/deploy-backend.sh
# ══════════════════════════════════════════════════════════════
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SEALED_DIR="$REPO_ROOT/k8s/sealed-secrets"
NS="mediconnect"

GREEN='\033[0;32m'; RED='\033[0;31m'; BLUE='\033[0;34m'; NC='\033[0m'
ok()  { echo -e "${GREEN}✅ $1${NC}"; }
err() { echo -e "${RED}❌ $1${NC}"; exit 1; }
hdr() { echo -e "\n${BLUE}══ $1 ══${NC}"; }

cd "$REPO_ROOT"

# ─────────────────────────────────────────────────────────────
# STEP 1 — Patch mediconnect-db-credentials
#          Add MONGODB_URI and POSTGRES_EXPORTER_DSN
# ─────────────────────────────────────────────────────────────
hdr "STEP 1: Patch mediconnect-db-credentials"

# Read the existing DB password from the already-deployed secret
DB_PASS=$(kubectl get secret mediconnect-db-credentials \
  -n $NS -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)

if [ -z "$DB_PASS" ]; then
  err "Could not read POSTGRES_PASSWORD from existing secret. Check namespace."
fi

echo "  Existing POSTGRES_PASSWORD found (length: ${#DB_PASS})"

MONGODB_URI="mongodb://mediconnect_user:${DB_PASS}@mongodb-service:27017/mediconnect?authSource=admin"
PG_EXPORTER_DSN="postgresql://mediconnect_user:${DB_PASS}@postgres-service:5432/mediconnect?sslmode=disable"

kubectl create secret generic mediconnect-db-credentials \
  --namespace $NS \
  --from-literal=POSTGRES_PASSWORD="$DB_PASS" \
  --from-literal=MONGODB_URI="$MONGODB_URI" \
  --from-literal=POSTGRES_EXPORTER_DSN="$PG_EXPORTER_DSN" \
  --dry-run=client -o yaml \
  | kubeseal --format yaml \
  > "$SEALED_DIR/db-credentials-sealed.yaml"

kubectl apply -f "$SEALED_DIR/db-credentials-sealed.yaml"
ok "mediconnect-db-credentials updated (3 keys)"

# ─────────────────────────────────────────────────────────────
# STEP 2 — Patch mediconnect-app-secrets
#          Add INTERNAL_SERVICE_TOKEN (used by WebSocket → Django)
# ─────────────────────────────────────────────────────────────
hdr "STEP 2: Patch mediconnect-app-secrets"

# Read existing SECRET_KEY
EXISTING_SK=$(kubectl get secret mediconnect-app-secrets \
  -n $NS -o jsonpath='{.data.SECRET_KEY}' | base64 -d)

# Generate a secure random token for WebSocket ↔ Django internal auth
INTERNAL_TOKEN=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
echo "  Generated INTERNAL_SERVICE_TOKEN: ${INTERNAL_TOKEN:0:12}..."

kubectl create secret generic mediconnect-app-secrets \
  --namespace $NS \
  --from-literal=SECRET_KEY="$EXISTING_SK" \
  --from-literal=INTERNAL_SERVICE_TOKEN="$INTERNAL_TOKEN" \
  --dry-run=client -o yaml \
  | kubeseal --format yaml \
  > "$SEALED_DIR/app-secrets-sealed.yaml"

kubectl apply -f "$SEALED_DIR/app-secrets-sealed.yaml"
ok "mediconnect-app-secrets updated (2 keys)"

# ─────────────────────────────────────────────────────────────
# STEP 3 — Commit updated sealed secrets
# ─────────────────────────────────────────────────────────────
hdr "STEP 3: Commit patched sealed secrets"
git add k8s/sealed-secrets/
git commit -m "fix: add missing MONGODB_URI, POSTGRES_EXPORTER_DSN, INTERNAL_SERVICE_TOKEN to sealed secrets" || echo "Nothing to commit"
git push
ok "Sealed secrets committed"

# ─────────────────────────────────────────────────────────────
# STEP 4 — Apply all K8s base manifests
# ─────────────────────────────────────────────────────────────
hdr "STEP 4: Apply Kubernetes base manifests"

MANIFESTS=(
  "k8s/base/namespace.yaml"
  "k8s/base/storageclass.yaml"
  "k8s/base/configmap.yaml"
  "k8s/base/postgres.yaml"
  "k8s/base/redis.yaml"
  "k8s/base/backend.yaml"
  "k8s/base/websocket.yaml"
  "k8s/base/frontend.yaml"
)

for manifest in "${MANIFESTS[@]}"; do
  if [ -f "$manifest" ]; then
    kubectl apply -f "$manifest"
    ok "Applied: $manifest"
  else
    echo "  ⚠️  Skipped (not found): $manifest"
  fi
done

# Apply ingress last (depends on all services existing)
if [ -f "k8s/base/ingress.yaml" ]; then
  kubectl apply -f "k8s/base/ingress.yaml"
  ok "Applied: k8s/base/ingress.yaml"
fi

# Apply HPA
if [ -f "k8s/base/hpa.yaml" ]; then
  kubectl apply -f "k8s/base/hpa.yaml"
  ok "Applied: k8s/base/hpa.yaml"
fi

# ─────────────────────────────────────────────────────────────
# STEP 5 — Wait for PostgreSQL to be ready
# ─────────────────────────────────────────────────────────────
hdr "STEP 5: Wait for PostgreSQL"

echo "  Waiting for postgres StatefulSet to be ready (up to 3 min)..."
kubectl rollout status statefulset/postgres -n $NS --timeout=180s || \
  err "PostgreSQL did not become ready in time"
ok "PostgreSQL is ready"

# ─────────────────────────────────────────────────────────────
# STEP 6 — Wait for backend pods to be running
# ─────────────────────────────────────────────────────────────
hdr "STEP 6: Wait for Backend"

echo "  Waiting for backend deployment (up to 3 min)..."
kubectl rollout status deployment/backend -n $NS --timeout=180s || \
  err "Backend deployment failed — check pod logs below:"

ok "Backend deployment ready"

# ─────────────────────────────────────────────────────────────
# STEP 7 — Run Django migrations
# ─────────────────────────────────────────────────────────────
hdr "STEP 7: Run Django Migrations"

BACKEND_POD=$(kubectl get pods -n $NS -l app=backend \
  --no-headers | grep Running | awk '{print $1}' | head -1)

if [ -z "$BACKEND_POD" ]; then
  err "No running backend pod found. Check: kubectl get pods -n $NS"
fi

echo "  Running migrations on pod: $BACKEND_POD"
kubectl exec -n $NS "$BACKEND_POD" -- \
  python manage.py migrate --noinput
ok "Migrations complete"

# ─────────────────────────────────────────────────────────────
# STEP 8 — Create Django superuser
# ─────────────────────────────────────────────────────────────
hdr "STEP 8: Create Superuser (Admin Account)"

echo "  Creating admin superuser..."
kubectl exec -n $NS "$BACKEND_POD" -- \
  python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@mediconnect.salman-aak.com').exists():
    User.objects.create_superuser(
        email='admin@mediconnect.salman-aak.com',
        username='admin',
        full_name='Ahmed Akinola Salman',
        phone='+2348000000000',
        role='admin',
        password='CHANGE_THIS_IMMEDIATELY!'
    )
    print('Superuser created')
else:
    print('Superuser already exists')
"
ok "Superuser ready — CHANGE THE PASSWORD at /admin/"

# ─────────────────────────────────────────────────────────────
# STEP 9 — Test API health endpoint
# ─────────────────────────────────────────────────────────────
hdr "STEP 9: Smoke Test"

# Test via kubectl port-forward (before DNS is set up)
echo "  Testing API health via port-forward..."
kubectl port-forward svc/backend-service 8000:8000 -n $NS &
PF_PID=$!
sleep 4

HEALTH=$(curl -s http://localhost:8000/api/v1/health/ 2>/dev/null || echo "{}")
STATUS=$(echo "$HEALTH" | python3 -c \
  "import sys,json; print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "")

kill $PF_PID 2>/dev/null || true

if [ "$STATUS" = "healthy" ]; then
  ok "API health check: $HEALTH"
else
  echo "  ⚠️  API returned: $HEALTH"
  echo "  Checking backend logs..."
  kubectl logs -n $NS "$BACKEND_POD" --tail=30
fi

# ─────────────────────────────────────────────────────────────
# STEP 10 — Print pod status
# ─────────────────────────────────────────────────────────────
hdr "STEP 10: Current Pod Status"

kubectl get pods -n $NS
echo ""
kubectl get services -n $NS

echo ""
echo "════════════════════════════════════════════════════════"
echo "  ✅ Backend deployment complete!"
echo ""
echo "  Next steps:"
echo "  1. Get the NGINX Ingress Load Balancer hostname:"
echo "     kubectl get svc ingress-nginx-controller -n ingress-nginx"
echo ""
echo "  2. Update terraform.tfvars with the LB hostname:"
echo "     ingress_lb_hostname = \"<ELB_HOSTNAME>\""
echo ""
echo "  3. Apply Terraform to set Route53 DNS:"
echo "     cd terraform/environments/production && terraform apply"
echo ""
echo "  4. Wait for DNS propagation (~2–5 min), then test:"
echo "     curl https://api.mediconnect.salman-aak.com/api/v1/health/"
echo ""
echo "  5. Change the admin password:"
echo "     https://mediconnect.salman-aak.com/admin/"
echo "     Email: admin@mediconnect.salman-aak.com"
echo "     Password: CHANGE_THIS_IMMEDIATELY!"
echo "════════════════════════════════════════════════════════"
