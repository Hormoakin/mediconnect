#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  MediConnect — Fix Empty Manifests + Continue Deployment
#  Run from repo root: bash scripts/fix-and-continue-deploy.sh
#
#  Picks up exactly where deploy-backend.sh stopped:
#  - Writes content into any empty k8s/base/*.yaml files
#  - Applies remaining manifests (websocket, frontend, ingress, hpa)
#  - Waits for backend, runs migrations, creates superuser
#  - Smoke tests the health endpoint
# ══════════════════════════════════════════════════════════════
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
NS="mediconnect"

GREEN='\033[0;32m'; RED='\033[0;31m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
err()  { echo -e "${RED}❌ $1${NC}"; exit 1; }
hdr()  { echo -e "\n${BLUE}══ $1 ══${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

cd "$REPO_ROOT"

# ─────────────────────────────────────────────────────────────
# STEP A — Write websocket.yaml (if empty or missing)
# ─────────────────────────────────────────────────────────────
hdr "STEP A: Populate k8s/base/websocket.yaml"

cat > k8s/base/websocket.yaml << 'WEBSOCKET_EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: websocket
  namespace: mediconnect
  labels:
    app: websocket
spec:
  replicas: 2
  selector:
    matchLabels:
      app: websocket
  template:
    metadata:
      labels:
        app: websocket
    spec:
      containers:
        - name: websocket
          image: hormoakin001/mediconnect-websocket:latest
          ports:
            - containerPort: 3001
          env:
            - name: PORT
              value: "3001"
            - name: CORS_ORIGIN
              value: "https://mediconnect.salman-aak.com"
            - name: REDIS_URL
              value: "redis://redis-service:6379/3"
            - name: DATABASE_HOST
              value: "postgres-service"
            - name: DATABASE_PORT
              value: "5432"
            - name: DATABASE_NAME
              value: "mediconnect"
            - name: DATABASE_USER
              value: "mediconnect_user"
            - name: BACKEND_INTERNAL_URL
              value: "http://backend-service:8000"
            - name: DATABASE_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mediconnect-db-credentials
                  key: POSTGRES_PASSWORD
            - name: JWT_SECRET
              valueFrom:
                secretKeyRef:
                  name: mediconnect-app-secrets
                  key: SECRET_KEY
            - name: INTERNAL_SERVICE_TOKEN
              valueFrom:
                secretKeyRef:
                  name: mediconnect-app-secrets
                  key: INTERNAL_SERVICE_TOKEN
          resources:
            requests:
              memory: "128Mi"
              cpu: "150m"
            limits:
              memory: "256Mi"
              cpu: "300m"
          livenessProbe:
            httpGet:
              path: /health
              port: 3001
            initialDelaySeconds: 15
            periodSeconds: 15
          readinessProbe:
            httpGet:
              path: /health
              port: 3001
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: websocket-service
  namespace: mediconnect
spec:
  selector:
    app: websocket
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800
  ports:
    - protocol: TCP
      port: 3001
      targetPort: 3001
WEBSOCKET_EOF
ok "k8s/base/websocket.yaml written"

# ─────────────────────────────────────────────────────────────
# STEP B — Write frontend.yaml (if empty or missing)
# ─────────────────────────────────────────────────────────────
hdr "STEP B: Populate k8s/base/frontend.yaml"

cat > k8s/base/frontend.yaml << 'FRONTEND_EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: mediconnect
  labels:
    app: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: frontend
          image: hormoakin001/mediconnect-frontend:latest
          ports:
            - containerPort: 80
          resources:
            requests:
              memory: "64Mi"
              cpu: "100m"
            limits:
              memory: "128Mi"
              cpu: "200m"
          livenessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 10
            periodSeconds: 15
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: mediconnect
spec:
  selector:
    app: frontend
  ports:
    - protocol: TCP
      port: 80
      targetPort: 80
FRONTEND_EOF
ok "k8s/base/frontend.yaml written"

# ─────────────────────────────────────────────────────────────
# STEP C — Write hpa.yaml (if empty or missing)
# ─────────────────────────────────────────────────────────────
hdr "STEP C: Populate k8s/base/hpa.yaml"

cat > k8s/base/hpa.yaml << 'HPA_EOF'
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: mediconnect
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: websocket-hpa
  namespace: mediconnect
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: websocket
  minReplicas: 2
  maxReplicas: 6
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 75
HPA_EOF
ok "k8s/base/hpa.yaml written"

# ─────────────────────────────────────────────────────────────
# STEP D — Verify ingress.yaml has content
# ─────────────────────────────────────────────────────────────
hdr "STEP D: Check k8s/base/ingress.yaml"

INGRESS_SIZE=$(wc -c < k8s/base/ingress.yaml 2>/dev/null || echo "0")
if [ "$INGRESS_SIZE" -lt 100 ]; then
  warn "ingress.yaml is empty — writing cert-manager ClusterIssuer + Ingress..."
  cat > k8s/base/ingress.yaml << 'INGRESS_EOF'
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ahmed@salman-aak.com
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
      - http01:
          ingress:
            class: nginx
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mediconnect-ingress
  namespace: mediconnect
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "120"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "120"
spec:
  tls:
    - hosts:
        - mediconnect.salman-aak.com
        - api.mediconnect.salman-aak.com
        - ws.mediconnect.salman-aak.com
      secretName: mediconnect-tls
  rules:
    - host: mediconnect.salman-aak.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 80
    - host: api.mediconnect.salman-aak.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: backend-service
                port:
                  number: 8000
    - host: ws.mediconnect.salman-aak.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: websocket-service
                port:
                  number: 3001
INGRESS_EOF
  ok "k8s/base/ingress.yaml written"
else
  ok "k8s/base/ingress.yaml already has content (${INGRESS_SIZE} bytes)"
fi

# ─────────────────────────────────────────────────────────────
# STEP E — Apply remaining manifests
# ─────────────────────────────────────────────────────────────
hdr "STEP E: Apply remaining manifests"

for f in \
  k8s/base/websocket.yaml \
  k8s/base/frontend.yaml \
  k8s/base/ingress.yaml \
  k8s/base/hpa.yaml; do
  kubectl apply -f "$f" && ok "Applied: $f"
done

# ─────────────────────────────────────────────────────────────
# STEP F — Commit all populated manifests to Git
# ─────────────────────────────────────────────────────────────
hdr "STEP F: Commit populated manifests"

git add k8s/base/
git diff --cached --quiet && echo "Nothing to commit" || {
  git commit -m "feat: populate k8s base manifests (websocket, frontend, ingress, hpa)"
  git push
  ok "Manifests committed and pushed"
}

# ─────────────────────────────────────────────────────────────
# STEP G — Wait for backend to be fully ready
# ─────────────────────────────────────────────────────────────
hdr "STEP G: Wait for Backend pods"

echo "  Waiting for backend deployment (up to 4 min)..."
kubectl rollout status deployment/backend -n $NS --timeout=240s || {
  warn "Backend rollout timed out. Checking pod events..."
  kubectl describe pods -n $NS -l app=backend | tail -30
  err "Backend not ready. Fix errors above then re-run."
}
ok "Backend ready"

# ─────────────────────────────────────────────────────────────
# STEP H — Run Django migrations
# ─────────────────────────────────────────────────────────────
hdr "STEP H: Django Migrations"

BACKEND_POD=$(kubectl get pods -n $NS -l app=backend \
  --no-headers | grep Running | awk '{print $1}' | head -1)

[ -z "$BACKEND_POD" ] && err "No running backend pod found."
echo "  Using pod: $BACKEND_POD"

kubectl exec -n $NS "$BACKEND_POD" -- \
  python manage.py migrate --noinput
ok "Migrations complete"

# ─────────────────────────────────────────────────────────────
# STEP I — Create superuser
# ─────────────────────────────────────────────────────────────
hdr "STEP I: Create Django Superuser"

kubectl exec -n $NS "$BACKEND_POD" -- python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
email = 'admin@mediconnect.salman-aak.com'
if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        email=email,
        username='admin',
        full_name='Ahmed Akinola Salman',
        phone='+2348103246469',
        role='admin',
        password='ChangeMe123!'
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"
ok "Superuser ready"

# ─────────────────────────────────────────────────────────────
# STEP J — Smoke test via port-forward
# ─────────────────────────────────────────────────────────────
hdr "STEP J: API Smoke Test"

kubectl port-forward svc/backend-service 8000:8000 -n $NS &
PF_PID=$!
sleep 4

HEALTH=$(curl -s --max-time 5 http://localhost:8000/api/v1/health/ 2>/dev/null || echo "{}")
STATUS=$(echo "$HEALTH" | python3 -c \
  "import sys,json; print(json.load(sys.stdin).get('status','error'))" 2>/dev/null || echo "error")

kill $PF_PID 2>/dev/null || true
wait $PF_PID 2>/dev/null || true

if [ "$STATUS" = "healthy" ]; then
  ok "API health: $HEALTH"
else
  warn "API health returned: $HEALTH"
  echo "  Showing last 20 log lines:"
  kubectl logs -n $NS "$BACKEND_POD" --tail=20
fi

# ─────────────────────────────────────────────────────────────
# FINAL STATUS
# ─────────────────────────────────────────────────────────────
hdr "Pod Status"
kubectl get pods -n $NS
echo ""
kubectl get svc -n $NS

echo ""
echo "════════════════════════════════════════════════════════"
echo "  ✅ Deployment continuation complete!"
echo ""
echo "  Next → Set up Route53 DNS:"
echo ""
echo "  1. Get the NGINX Ingress LB hostname:"
echo "     kubectl get svc ingress-nginx-controller -n ingress-nginx"
echo ""
echo "  2. Update terraform/environments/production/terraform.tfvars:"
echo "     ingress_lb_hostname = \"<paste ELB hostname here>\""
echo ""
echo "  3. Apply Terraform:"
echo "     cd terraform/environments/production && terraform apply"
echo ""
echo "  4. Test live (after DNS ~2-5 min):"
echo "     curl https://api.mediconnect.salman-aak.com/api/v1/health/"
echo ""
echo "  ⚠️  Change admin password immediately:"
echo "     https://mediconnect.salman-aak.com/admin/"
echo "     Email:    admin@mediconnect.salman-aak.com"
echo "     Password: ChangeMe123!"
echo "════════════════════════════════════════════════════════"
