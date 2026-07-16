#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  MediConnect — Monitoring Stack Deployment Guide
#  Run after Phase 1 (cluster up) and after sealed secrets
#  from Phase 2 are already applied.
# ══════════════════════════════════════════════════════════════
set -e

# ── STEP 1: Seal the Grafana admin password ────────────────────
echo "🔐 Sealing Grafana admin password..."

GRAFANA_PASSWORD="MediConnect@Grafana2026!"   # Change this

kubectl create secret generic grafana-secrets \
  --namespace monitoring \
  --from-literal=admin_password="${GRAFANA_PASSWORD}" \
  --dry-run=client -o yaml \
  | kubeseal --format yaml > k8s/sealed-secrets/grafana-secrets-sealed.yaml

kubectl apply -f k8s/sealed-secrets/grafana-secrets-sealed.yaml

echo "✅ Grafana secret sealed and applied"

# ── STEP 2: Deploy the monitoring namespace + stack ────────────
echo "📦 Deploying monitoring namespace..."
kubectl apply -f k8s/monitoring/namespace.yaml  # (already has monitoring ns)

echo "📦 Deploying Prometheus RBAC..."
kubectl apply -f k8s/monitoring/prometheus-rbac.yaml

echo "📦 Deploying Prometheus ConfigMap (config + alert rules)..."
kubectl apply -f k8s/monitoring/prometheus-config.yaml

echo "📦 Deploying Prometheus..."
kubectl apply -f k8s/monitoring/prometheus-deployment.yaml

echo "📦 Deploying Grafana datasource + dashboard configs..."
kubectl apply -f k8s/monitoring/grafana.yaml

echo "📦 Deploying Alertmanager..."
kubectl apply -f k8s/monitoring/alertmanager.yaml

echo "📦 Deploying postgres_exporter and redis_exporter..."
kubectl apply -f k8s/monitoring/exporters.yaml

# ── STEP 3: Wait for all monitoring pods to be ready ──────────
echo "⏳ Waiting for monitoring pods..."
kubectl wait --for=condition=ready pod -l app=prometheus   -n monitoring --timeout=120s
kubectl wait --for=condition=ready pod -l app=grafana      -n monitoring --timeout=120s
kubectl wait --for=condition=ready pod -l app=alertmanager -n monitoring --timeout=120s

echo ""
kubectl get pods -n monitoring

# ── STEP 4: Add Grafana ingress route to NGINX ─────────────────
echo ""
echo "📝 Add Grafana to your ingress.yaml under rules:"
echo "    - host: grafana.mediconnect.salman-aak.com"
echo "      http:"
echo "        paths:"
echo "          - path: /"
echo "            pathType: Prefix"
echo "            backend:"
echo "              service:"
echo "                name: grafana-service"
echo "                port:"
echo "                  number: 3000"
echo ""
echo "Then add to tls.hosts in ingress.yaml:"
echo "    - grafana.mediconnect.salman-aak.com"
echo ""
echo "And add a Route53 CNAME in terraform.tfvars:"
echo '    resource "aws_route53_record" "grafana" {'
echo '      name    = "grafana.mediconnect.salman-aak.com"'
echo '      type    = "CNAME"'
echo '      records = [var.ingress_lb_hostname]'
echo '    }'
echo ""
echo "Then: terraform apply"

# ── STEP 5: Verify Prometheus targets ─────────────────────────
echo ""
echo "🔍 Verify Prometheus is scraping all targets:"
echo "   kubectl port-forward svc/prometheus-service 9090:9090 -n monitoring"
echo "   Then open: http://localhost:9090/targets"
echo ""
echo "   You should see green (UP) for:"
echo "   ✅ mediconnect-backend"
echo "   ✅ kubernetes-nodes"
echo "   ✅ kubernetes-cadvisor"
echo "   ✅ postgresql"
echo "   ✅ redis"
echo "   ✅ nginx-ingress"
echo "   ✅ node-exporter"

# ── STEP 6: Verify Grafana dashboards ─────────────────────────
echo ""
echo "📊 Access Grafana:"
echo "   kubectl port-forward svc/grafana-service 3000:3000 -n monitoring"
echo "   Then open: http://localhost:3000"
echo "   Username:  admin"
echo "   Password:  ${GRAFANA_PASSWORD}"
echo ""
echo "   Or via ingress: https://grafana.mediconnect.salman-aak.com"
echo "   (after Terraform apply + DNS propagation)"
