#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  MediConnect — Phase 3 Complete Execution Guide
#  Covers: WebSocket service, React frontend, Ansible hardening,
#          Prometheus + Grafana monitoring.
#
#  Prerequisites: Phase 1 (cluster up) + Phase 2 (Django backend
#  deployed) are both complete and healthy.
# ══════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────
# PART A — WebSocket Service (Socket.io)
# ─────────────────────────────────────────────────────────────
echo "═══ PART A: WebSocket Service ═══"

# A1. Place files
# websocket_service/package.json      ← websocket-package.json
# websocket_service/Dockerfile        ← websocket-Dockerfile
# websocket_service/server.js         ← websocket-server.js
# websocket_service/config.js         ← websocket-config-auth.js (first section)
# websocket_service/middleware/auth.js ← websocket-config-auth.js (second section)
# websocket_service/handlers/message.js     ← websocket-handler-message.js
# websocket_service/handlers/notification.js ← websocket-handler-notification.js
# backend/apps/notifications/internal_views.py ← backend-internal-notify-view.py

# A2. Test locally with Docker Compose
cd websocket_service && npm install && cd ..
docker compose up -d websocket
docker compose logs websocket --tail=20

# A3. Build and push Docker image
docker buildx build \
  --platform linux/amd64 \
  --tag hormoakin001/mediconnect-websocket:latest \
  --push \
  ./websocket_service

# A4. Apply K8s manifest
kubectl apply -f k8s/base/websocket.yaml
kubectl rollout status deployment/websocket -n mediconnect

# A5. Verify health
kubectl get pods -n mediconnect -l app=websocket
# Should show 2/2 Running

# ─────────────────────────────────────────────────────────────
# PART B — React Frontend
# ─────────────────────────────────────────────────────────────
echo ""
echo "═══ PART B: React Frontend ═══"

# B1. Place files (use the config-files.txt as reference —
#     copy each section between the /* ... */ markers into its
#     corresponding file path)
# frontend/package.json              ← frontend-package.json
# frontend/vite.config.ts            ← from frontend-config-files.txt
# frontend/tsconfig.json             ← from frontend-config-files.txt
# frontend/tailwind.config.js        ← from frontend-config-files.txt
# frontend/postcss.config.js         ← from frontend-config-files.txt
# frontend/index.html                ← from frontend-config-files.txt
# frontend/Dockerfile                ← from frontend-config-files.txt
# frontend/nginx.conf                ← from frontend-config-files.txt
# frontend/src/main.tsx              ← frontend-src-main-app.tsx (first section)
# frontend/src/index.css             ← frontend-src-main-app.tsx (CSS section)
# frontend/src/App.tsx               ← frontend-src-main-app.tsx (App section)
# frontend/src/types/user.ts         ← frontend-types.ts (split by type file)
# frontend/src/types/appointment.ts  ← frontend-types.ts
# frontend/src/types/prescription.ts ← frontend-types.ts
# frontend/src/types/record.ts       ← frontend-types.ts
# frontend/src/types/message.ts      ← frontend-types.ts
# frontend/src/types/ai.ts           ← frontend-types.ts
# frontend/src/services/api.ts       ← frontend-services.ts
# frontend/src/services/auth.ts, doctors.ts, appointments.ts,
#   ai.ts, prescriptions.ts, records.ts, messages.ts
#                                    ← frontend-services.ts (split by service)
# frontend/src/contexts/AuthContext.tsx  ← frontend-contexts.tsx
# frontend/src/contexts/SocketContext.tsx ← frontend-contexts.tsx
# frontend/src/components/common/ProtectedRoute.tsx ← frontend-common-components.tsx
# frontend/src/components/common/LoadingSpinner.tsx ← frontend-common-components.tsx
# frontend/src/components/common/EmptyState.tsx     ← frontend-common-components.tsx
# frontend/src/components/common/StatusBadge.tsx    ← frontend-common-components.tsx
# frontend/src/components/layout/DashboardLayout.tsx ← frontend-dashboard-layout.tsx
# frontend/src/pages/Landing.tsx              ← frontend-Landing.tsx
# frontend/src/pages/auth/Login.tsx           ← frontend-auth-pages.tsx
# frontend/src/pages/auth/Register.tsx        ← frontend-auth-pages.tsx
# frontend/src/pages/patient/PatientDashboard.tsx ← frontend-patient-pages.tsx
# frontend/src/pages/patient/FindDoctors.tsx      ← frontend-patient-pages.tsx
# frontend/src/pages/patient/SymptomChecker.tsx   ← frontend-patient-pages.tsx
# frontend/src/pages/doctor/DoctorDashboard.tsx   ← frontend-remaining-pages.tsx
# frontend/src/pages/pharmacist/PharmacistDashboard.tsx ← frontend-remaining-pages.tsx
# frontend/src/pages/admin/AdminDashboard.tsx      ← frontend-remaining-pages.tsx
# frontend/src/pages/Chat.tsx                      ← frontend-remaining-pages.tsx
# frontend/src/pages/MedicalRecords.tsx            ← frontend-remaining-pages.tsx
# frontend/src/components/forms/BookAppointmentModal.tsx ← frontend-remaining-pages.tsx

# B2. Install dependencies and test locally
cd frontend
npm install
npm run dev
# Open http://localhost:5173 — you should see the Landing page

# B3. Build production image
docker buildx build \
  --platform linux/amd64 \
  --target production \
  --tag hormoakin001/mediconnect-frontend:latest \
  --push \
  ./frontend

# B4. Apply frontend K8s manifest
kubectl apply -f k8s/base/frontend.yaml
kubectl rollout status deployment/frontend -n mediconnect

# B5. Apply ingress (routes / to frontend, /api to backend, /ws to websocket)
kubectl apply -f k8s/base/ingress.yaml
kubectl get ingress -n mediconnect

# ─────────────────────────────────────────────────────────────
# PART C — Ansible Node Hardening
# ─────────────────────────────────────────────────────────────
echo ""
echo "═══ PART C: Ansible Node Hardening ═══"

# C1. Place files:
# ansible/site.yml                      ← ansible-site-inventory.yml (site.yml section)
# ansible/inventory/hosts               ← ansible-site-inventory.yml (hosts section)
# ansible/roles/common/tasks/main.yml   ← ansible-role-common.yml
# ansible/roles/security/tasks/main.yml ← ansible-role-security.yml
# ansible/roles/monitoring/tasks/main.yml ← ansible-role-monitoring.yml

# C2. Get node IPs
kubectl get nodes -o wide
# Note the INTERNAL-IP column for each node

# C3. Update ansible/inventory/hosts with the real node IPs
# The nodes are in private subnets — access via SSH through
# the bastion host or via AWS SSM Session Manager:
#
#   aws ssm start-session --target i-INSTANCE_ID
#
# For Ansible, add this to ansible/inventory/hosts:
#   [all:vars]
#   ansible_ssh_common_args='-o ProxyJump=ubuntu@BASTION_IP'

# C4. Run the playbook (--check first to preview changes)
ansible-playbook -i ansible/inventory/hosts ansible/site.yml \
  --private-key ~/.ssh/mediconnect_nodes \
  --become \
  --check      # Preview mode — remove --check to apply

# C5. Apply for real
ansible-playbook -i ansible/inventory/hosts ansible/site.yml \
  --private-key ~/.ssh/mediconnect_nodes \
  --become

# C6. Verify hardening on one node (pick any worker)
# Check SSH config
ansible workers[0] -i ansible/inventory/hosts -m command \
  -a "sshd -T | grep -E 'permitrootlogin|passwordauthentication|maxauthtries'" \
  --become

# Check fail2ban is active
ansible all -i ansible/inventory/hosts -m command \
  -a "fail2ban-client status sshd" --become

# Check UFW status
ansible all -i ansible/inventory/hosts -m command \
  -a "ufw status verbose" --become

# Check node_exporter is running
ansible all -i ansible/inventory/hosts -m uri \
  -a "url=http://localhost:9100/metrics return_content=no"

# ─────────────────────────────────────────────────────────────
# PART D — Prometheus + Grafana Monitoring Stack
# ─────────────────────────────────────────────────────────────
echo ""
echo "═══ PART D: Monitoring Stack ═══"

# D1. Place files:
# k8s/monitoring/prometheus-config.yaml    ← k8s-monitoring-stack.yaml (ConfigMap section)
# k8s/monitoring/prometheus-deployment.yaml ← k8s-monitoring-stack.yaml (Deployment section)
# k8s/monitoring/grafana.yaml              ← k8s-monitoring-stack.yaml (Grafana sections)
# k8s/monitoring/alertmanager.yaml         ← k8s-monitoring-stack.yaml (Alertmanager section)
# k8s/monitoring/exporters.yaml            ← k8s-monitoring-exporters.yaml

# D2. Run the deployment guide script
bash deploy-monitoring-stack.sh

# ─────────────────────────────────────────────────────────────
# PART E — End-to-End Phase 3 Verification
# ─────────────────────────────────────────────────────────────
echo ""
echo "═══ PART E: End-to-End Verification ═══"

# E1. Check all pods across all namespaces
kubectl get pods -A | grep -v "Running\|Completed" || echo "✅ All pods healthy"
kubectl get pods -n mediconnect
kubectl get pods -n monitoring

# E2. Test WebSocket connection
cat << 'EOF'
Test WebSocket from browser console:
  const socket = io("https://ws.mediconnect.salman-aak.com", {
    auth: { token: "YOUR_JWT_TOKEN" }
  });
  socket.on("connect", () => console.log("✅ WebSocket connected"));
  socket.on("connect_error", (err) => console.error("❌", err.message));
EOF

# E3. Smoke test the full stack
echo ""
echo "Running smoke tests..."

# Frontend
FRONT=$(curl -s -o /dev/null -w "%{http_code}" https://mediconnect.salman-aak.com)
echo "Frontend (mediconnect.salman-aak.com): HTTP $FRONT"

# Backend API health
API=$(curl -s -o /dev/null -w "%{http_code}" https://api.mediconnect.salman-aak.com/api/v1/health/)
echo "Backend API /health:                   HTTP $API"

# WebSocket health
WS=$(curl -s -o /dev/null -w "%{http_code}" https://ws.mediconnect.salman-aak.com/health)
echo "WebSocket /health:                     HTTP $WS"

# E4. Verify Prometheus scraping
echo ""
echo "📊 Verify Prometheus targets:"
kubectl port-forward svc/prometheus-service 9090:9090 -n monitoring &
sleep 3
curl -s http://localhost:9090/api/v1/targets | python3 -c "
import json, sys
data = json.load(sys.stdin)
targets = data.get('data', {}).get('activeTargets', [])
for t in targets:
    status = '✅' if t['health'] == 'up' else '❌'
    print(f\"{status} {t['labels'].get('job', 'unknown')} — {t['health']}\")
"
kill %1 2>/dev/null

echo ""
echo "════════════════════════════════════════════════"
echo "  🎉 Phase 3 COMPLETE!"
echo ""
echo "  Live URLs:"
echo "  Frontend:   https://mediconnect.salman-aak.com"
echo "  API:        https://api.mediconnect.salman-aak.com/api/v1/health/"
echo "  WebSocket:  https://ws.mediconnect.salman-aak.com/health"
echo "  Grafana:    https://grafana.mediconnect.salman-aak.com"
echo ""
echo "  Next → Phase 4: AI Service (FastAPI) + full integration tests"
echo "════════════════════════════════════════════════"
