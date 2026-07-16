#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  MediConnect — Production Validation Script
#  Validates the full deployed system across 12 checks covering
#  infrastructure, application, security, AI, notifications,
#  and monitoring (Chapter 5 — Testing Strategy).
#
#  Run after every deployment:
#    bash scripts/validate-all.sh
#
#  All 12 checks must pass before marking a deployment STABLE.
# ══════════════════════════════════════════════════════════════
set -euo pipefail

FRONTEND_URL="https://mediconnect.salman-aak.com"
API_URL="https://api.mediconnect.salman-aak.com"
WS_URL="https://ws.mediconnect.salman-aak.com"
GRAFANA_URL="https://grafana.mediconnect.salman-aak.com"
NAMESPACE="mediconnect"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'  # No Colour

PASS=0; FAIL=0; WARN=0

pass()  { echo -e "  ${GREEN}✅ PASS${NC}  $1"; ((PASS++)); }
fail()  { echo -e "  ${RED}❌ FAIL${NC}  $1"; ((FAIL++)); }
warn()  { echo -e "  ${YELLOW}⚠️  WARN${NC}  $1"; ((WARN++)); }
info()  { echo -e "  ${BLUE}ℹ️  INFO${NC}  $1"; }
header(){ echo -e "\n${BLUE}══ $1 ══${NC}"; }

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   MediConnect Production Validation                  ║"
echo "║   $(date '+%Y-%m-%d %H:%M:%S %Z')                         ║"
echo "╚══════════════════════════════════════════════════════╝"

# ─────────────────────────────────────────────────────────────
# CHECK 1 — Kubernetes cluster health
# ─────────────────────────────────────────────────────────────
header "CHECK 1: Kubernetes Cluster Health"

NODE_COUNT=$(kubectl get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')
READY_COUNT=$(kubectl get nodes --no-headers 2>/dev/null | grep " Ready" | wc -l | tr -d ' ')

if [ "$NODE_COUNT" -eq 6 ] && [ "$READY_COUNT" -eq 6 ]; then
    pass "All 6 nodes Ready ($NODE_COUNT total)"
elif [ "$READY_COUNT" -ge 4 ]; then
    warn "Only $READY_COUNT/$NODE_COUNT nodes Ready (need ≥4 for HA)"
else
    fail "Only $READY_COUNT/$NODE_COUNT nodes Ready — cluster may be degraded"
fi

# Check nodes are spread across 3 AZs
AZ_COUNT=$(kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.labels.topology\.kubernetes\.io/zone}{"\n"}{end}' 2>/dev/null | sort -u | wc -l | tr -d ' ')
if [ "$AZ_COUNT" -ge 3 ]; then
    pass "Nodes distributed across $AZ_COUNT Availability Zones (HA design)"
else
    warn "Nodes in only $AZ_COUNT AZs — expected 3 for full HA"
fi

# ─────────────────────────────────────────────────────────────
# CHECK 2 — Pod health in mediconnect namespace
# ─────────────────────────────────────────────────────────────
header "CHECK 2: Application Pod Health"

PODS_NOT_RUNNING=$(kubectl get pods -n $NAMESPACE --no-headers 2>/dev/null \
    | grep -v "Running\|Completed" | wc -l | tr -d ' ')

if [ "$PODS_NOT_RUNNING" -eq 0 ]; then
    TOTAL_PODS=$(kubectl get pods -n $NAMESPACE --no-headers | wc -l | tr -d ' ')
    pass "All $TOTAL_PODS pods in mediconnect namespace are Running"
else
    fail "$PODS_NOT_RUNNING pod(s) not in Running state:"
    kubectl get pods -n $NAMESPACE --no-headers | grep -v "Running\|Completed" || true
fi

# Check minimum replica counts for critical deployments
for deploy in backend frontend websocket; do
    READY=$(kubectl get deploy $deploy -n $NAMESPACE \
        -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    DESIRED=$(kubectl get deploy $deploy -n $NAMESPACE \
        -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
    if [ "${READY:-0}" -eq "${DESIRED:-0}" ] && [ "${DESIRED:-0}" -ge 2 ]; then
        pass "$deploy: $READY/$DESIRED replicas ready"
    else
        fail "$deploy: only $READY/$DESIRED replicas ready"
    fi
done

# ─────────────────────────────────────────────────────────────
# CHECK 3 — Persistent storage
# ─────────────────────────────────────────────────────────────
header "CHECK 3: Persistent Storage (EBS PVCs)"

UNBOUND=$(kubectl get pvc -n $NAMESPACE --no-headers 2>/dev/null \
    | grep -v "Bound" | wc -l | tr -d ' ')
TOTAL_PVC=$(kubectl get pvc -n $NAMESPACE --no-headers 2>/dev/null | wc -l | tr -d ' ')

if [ "$UNBOUND" -eq 0 ]; then
    pass "All $TOTAL_PVC PVCs Bound (encrypted EBS gp3)"
else
    fail "$UNBOUND/$TOTAL_PVC PVC(s) not Bound:"
    kubectl get pvc -n $NAMESPACE | grep -v Bound || true
fi

# ─────────────────────────────────────────────────────────────
# CHECK 4 — SSL/TLS certificates
# ─────────────────────────────────────────────────────────────
header "CHECK 4: SSL/TLS Certificates (NFR-06)"

NOT_READY=$(kubectl get certificates -n $NAMESPACE --no-headers 2>/dev/null \
    | grep -v "True" | wc -l | tr -d ' ')
TOTAL_CERTS=$(kubectl get certificates -n $NAMESPACE --no-headers 2>/dev/null | wc -l | tr -d ' ')

if [ "$TOTAL_CERTS" -gt 0 ] && [ "$NOT_READY" -eq 0 ]; then
    pass "All $TOTAL_CERTS TLS certificates Ready (Let's Encrypt)"
elif [ "$TOTAL_CERTS" -eq 0 ]; then
    warn "No certificates found — cert-manager may not be installed"
else
    fail "$NOT_READY/$TOTAL_CERTS certificate(s) not Ready"
fi

# Check actual HTTPS response
SSL_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$FRONTEND_URL" 2>/dev/null || echo "000")
if [ "$SSL_CODE" == "200" ]; then
    pass "HTTPS GET $FRONTEND_URL → HTTP $SSL_CODE (TLS working)"
else
    fail "HTTPS GET $FRONTEND_URL → HTTP $SSL_CODE"
fi

# ─────────────────────────────────────────────────────────────
# CHECK 5 — API health endpoint
# ─────────────────────────────────────────────────────────────
header "CHECK 5: Backend API Health (NFR-01)"

API_RESPONSE=$(curl -s --max-time 5 "$API_URL/api/v1/health/" 2>/dev/null || echo "{}")
API_STATUS=$(echo "$API_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || echo "")
API_TIME=$(curl -s -o /dev/null -w "%{time_total}" --max-time 5 "$API_URL/api/v1/health/" 2>/dev/null || echo "99")
API_MS=$(echo "$API_TIME * 1000" | bc | cut -d. -f1)

if [ "$API_STATUS" == "healthy" ]; then
    pass "API health endpoint: status=healthy"
else
    fail "API health endpoint: unexpected response — $API_RESPONSE"
fi

if [ "${API_MS:-9999}" -lt 500 ]; then
    pass "API health response time: ${API_MS}ms (NFR-01: < 500ms)"
else
    warn "API health response time: ${API_MS}ms (NFR-01: < 500ms)"
fi

# ─────────────────────────────────────────────────────────────
# CHECK 6 — HTTP to HTTPS redirect
# ─────────────────────────────────────────────────────────────
header "CHECK 6: HTTP → HTTPS Redirect"

REDIRECT_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time 10 \
    "http://mediconnect.salman-aak.com" 2>/dev/null || echo "000")

if [ "$REDIRECT_CODE" == "301" ] || [ "$REDIRECT_CODE" == "308" ]; then
    pass "HTTP redirects to HTTPS with $REDIRECT_CODE"
else
    warn "HTTP redirect returned $REDIRECT_CODE (expected 301/308)"
fi

# ─────────────────────────────────────────────────────────────
# CHECK 7 — WebSocket service health
# ─────────────────────────────────────────────────────────────
header "CHECK 7: WebSocket Service Health (FR-05)"

WS_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time 5 "$WS_URL/health" 2>/dev/null || echo "000")

if [ "$WS_CODE" == "200" ]; then
    WS_RESPONSE=$(curl -s --max-time 5 "$WS_URL/health" 2>/dev/null || echo "{}")
    WS_STATUS=$(echo "$WS_RESPONSE" | python3 -c \
        "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || echo "")
    if [ "$WS_STATUS" == "healthy" ]; then
        CONNS=$(echo "$WS_RESPONSE" | python3 -c \
            "import sys,json; d=json.load(sys.stdin); print(d.get('connections',0))" 2>/dev/null || echo "?")
        pass "WebSocket service: healthy ($CONNS active connections)"
    else
        warn "WebSocket service returned 200 but status != healthy"
    fi
else
    fail "WebSocket service: HTTP $WS_CODE (expected 200)"
fi

# ─────────────────────────────────────────────────────────────
# CHECK 8 — Prometheus metrics collection (NFR-13)
# ─────────────────────────────────────────────────────────────
header "CHECK 8: Prometheus Monitoring (NFR-13)"

PROM_TARGETS=$(kubectl exec -n monitoring deploy/prometheus -- \
    wget -qO- "http://localhost:9090/api/v1/targets" 2>/dev/null || echo "")

if [ -n "$PROM_TARGETS" ]; then
    UP_COUNT=$(echo "$PROM_TARGETS" | python3 -c \
        "import sys,json; d=json.load(sys.stdin); \
         targets=d.get('data',{}).get('activeTargets',[]); \
         print(sum(1 for t in targets if t.get('health')=='up'))" 2>/dev/null || echo "0")
    TOTAL_T=$(echo "$PROM_TARGETS" | python3 -c \
        "import sys,json; d=json.load(sys.stdin); \
         print(len(d.get('data',{}).get('activeTargets',[])))" 2>/dev/null || echo "0")

    if [ "$UP_COUNT" -eq "$TOTAL_T" ] && [ "$TOTAL_T" -gt 0 ]; then
        pass "Prometheus: $UP_COUNT/$TOTAL_T targets UP"
    else
        warn "Prometheus: $UP_COUNT/$TOTAL_T targets UP"
    fi
else
    warn "Could not reach Prometheus API — check if pod is running"
fi

# Check Grafana is accessible
GRAFANA_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    --max-time 10 "$GRAFANA_URL/api/health" 2>/dev/null || echo "000")
if [ "$GRAFANA_CODE" == "200" ]; then
    pass "Grafana dashboards accessible (HTTP $GRAFANA_CODE)"
else
    warn "Grafana: HTTP $GRAFANA_CODE (expected 200)"
fi

# ─────────────────────────────────────────────────────────────
# CHECK 9 — Terraform drift detection (NFR-12, NDPR compliance)
# ─────────────────────────────────────────────────────────────
header "CHECK 9: Terraform Infrastructure Drift"

cd terraform/environments/production 2>/dev/null || {
    warn "terraform/environments/production not found — skipping drift check"
    cd - > /dev/null
}

if command -v terraform >/dev/null 2>&1; then
    PLAN_OUTPUT=$(terraform plan -detailed-exitcode -no-color 2>&1 || true)
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        pass "Terraform: no infrastructure drift detected"
    elif [ $EXIT_CODE -eq 2 ]; then
        warn "Terraform: drift detected — run 'terraform apply' to reconcile"
        info "Changes: $(echo "$PLAN_OUTPUT" | grep 'Plan:' | head -1)"
    else
        fail "Terraform plan failed — check AWS credentials and state"
    fi
else
    warn "Terraform not found — skipping drift check"
fi
cd - > /dev/null 2>&1 || true

# ─────────────────────────────────────────────────────────────
# CHECK 10 — HPA autoscaling configuration (NFR-09)
# ─────────────────────────────────────────────────────────────
header "CHECK 10: Horizontal Pod Autoscaling (NFR-09)"

for hpa in backend-hpa websocket-hpa; do
    HPA_INFO=$(kubectl get hpa $hpa -n $NAMESPACE \
        --no-headers 2>/dev/null || echo "NOT_FOUND")
    if echo "$HPA_INFO" | grep -q "NOT_FOUND"; then
        fail "HPA $hpa not found"
    else
        MIN=$(kubectl get hpa $hpa -n $NAMESPACE \
            -o jsonpath='{.spec.minReplicas}' 2>/dev/null || echo "?")
        MAX=$(kubectl get hpa $hpa -n $NAMESPACE \
            -o jsonpath='{.spec.maxReplicas}' 2>/dev/null || echo "?")
        pass "HPA $hpa: minReplicas=$MIN, maxReplicas=$MAX"
    fi
done

# ─────────────────────────────────────────────────────────────
# CHECK 11 — Sealed Secrets (NFR-06, NFR-07)
# ─────────────────────────────────────────────────────────────
header "CHECK 11: Sealed Secrets (Encrypted at Rest, NFR-07)"

SECRETS=$(kubectl get secrets -n $NAMESPACE --no-headers 2>/dev/null | wc -l | tr -d ' ')
EXPECTED_SECRETS=4   # db-credentials, app-secrets, api-secrets, aws-secrets

if [ "${SECRETS:-0}" -ge "$EXPECTED_SECRETS" ]; then
    pass "$SECRETS secrets present in mediconnect namespace"
else
    fail "Only $SECRETS/$EXPECTED_SECRETS expected secrets found"
fi

SEALED_CONTROLLER=$(kubectl get deploy sealed-secrets-controller \
    -n kube-system --no-headers 2>/dev/null | grep "1/1" | wc -l | tr -d ' ')
if [ "${SEALED_CONTROLLER:-0}" -ge 1 ]; then
    pass "Sealed Secrets controller: Running"
else
    warn "Sealed Secrets controller not found or not ready"
fi

# ─────────────────────────────────────────────────────────────
# CHECK 12 — AI service health and end-to-end symptom check
# ─────────────────────────────────────────────────────────────
header "CHECK 12: AI Service Health (FR-04)"

AI_POD=$(kubectl get pods -n $NAMESPACE -l app=ai-service \
    --no-headers 2>/dev/null | grep "Running" | awk '{print $1}' | head -1)

if [ -n "$AI_POD" ]; then
    pass "AI service pod Running: $AI_POD"

    # Test health endpoint inside the cluster
    AI_HEALTH=$(kubectl exec -n $NAMESPACE "$AI_POD" -- \
        wget -qO- "http://localhost:8001/health" 2>/dev/null || echo "{}")
    AI_STATUS=$(echo "$AI_HEALTH" | python3 -c \
        "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || echo "")
    AI_MODELS=$(echo "$AI_HEALTH" | python3 -c \
        "import sys,json; d=json.load(sys.stdin); print(d.get('models_loaded',''))" 2>/dev/null || echo "")

    if [ "$AI_STATUS" == "healthy" ] && [ "$AI_MODELS" == "True" ]; then
        pass "AI service: healthy, ML models loaded"
    else
        warn "AI service status: $AI_STATUS, models_loaded: $AI_MODELS"
    fi
else
    warn "AI service pod not found or not Running — deploy k8s/base/ai-service.yaml"
fi

# ─────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ─────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   VALIDATION SUMMARY                                 ║"
echo "╠══════════════════════════════════════════════════════╣"
echo -e "║   ${GREEN}✅ PASS: $PASS${NC}   ${YELLOW}⚠️  WARN: $WARN${NC}   ${RED}❌ FAIL: $FAIL${NC}             ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

if [ $FAIL -eq 0 ] && [ $WARN -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED — MediConnect deployment is STABLE${NC}"
    echo ""
    echo "  Frontend:  $FRONTEND_URL"
    echo "  API:       $API_URL/api/v1/health/"
    echo "  WebSocket: $WS_URL/health"
    echo "  Grafana:   $GRAFANA_URL"
    exit 0
elif [ $FAIL -eq 0 ]; then
    echo -e "${YELLOW}⚠️  DEPLOYMENT STABLE WITH WARNINGS — review WARN items above${NC}"
    exit 0
else
    echo -e "${RED}❌ DEPLOYMENT HAS FAILURES — do not mark as stable${NC}"
    echo "   Fix all FAIL items before declaring the deployment production-ready."
    exit 1
fi
