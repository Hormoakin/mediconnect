#!/bin/bash
# ══════════════════════════════════════════════════════════════
#  MediConnect — Phase 1 Step-by-Step Commands
#  Copy and run each section in your terminal
# ══════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────
# STEP 1: Create GitHub Repo
# Go to: https://github.com/new
# Name: mediconnect
# Visibility: Public
# Do NOT initialise with README (we'll push our own)
# ─────────────────────────────────────────────────────────────

# STEP 2: Run the scaffold script
chmod +x mediconnect-scaffold.sh
bash mediconnect-scaffold.sh

# STEP 3: Initialise Git and push scaffold
cd mediconnect
git init
git add .
git commit -m "chore: initial project scaffold"
git branch -M main
git remote add origin git@github.com:Hormoakin/mediconnect.git
git push -u origin main

# ─────────────────────────────────────────────────────────────
# STEP 4: Create Kops state bucket (BEFORE terraform init)
# ─────────────────────────────────────────────────────────────
aws s3 mb s3://mediconnect-kops-state-aak --region eu-north-1
aws s3api put-bucket-versioning \
  --bucket mediconnect-kops-state-aak \
  --versioning-configuration Status=Enabled

# STEP 5: Bootstrap Terraform (creates state bucket + DynamoDB)
# Copy terraform-main.tf, terraform-variables.tf, terraform-backend.tf
# into terraform/environments/production/ then:

cd terraform/environments/production

# First run WITHOUT backend (to create the bucket itself)
terraform init -backend=false
terraform apply -target=aws_s3_bucket.terraform_state \
                -target=aws_s3_bucket_versioning.terraform_state \
                -target=aws_s3_bucket_server_side_encryption_configuration.terraform_state \
                -target=aws_s3_bucket_public_access_block.terraform_state \
                -target=aws_dynamodb_table.terraform_locks \
                -auto-approve

# Now re-init WITH the S3 backend
terraform init
# Type 'yes' to migrate state to S3

# ─────────────────────────────────────────────────────────────
# STEP 6: Create SSH key for Kops cluster nodes
# ─────────────────────────────────────────────────────────────
ssh-keygen -t rsa -b 4096 -f ~/.ssh/mediconnect_nodes -N ""
echo "Public key:"
cat ~/.ssh/mediconnect_nodes.pub

# ─────────────────────────────────────────────────────────────
# STEP 7: Set Kops environment variables
# ─────────────────────────────────────────────────────────────
export CLUSTER_NAME="mediconnect.k8s.local"
export KOPS_STATE_STORE="s3://mediconnect-kops-state-aak"

# Add to ~/.zshrc or ~/.bashrc so they persist:
echo 'export CLUSTER_NAME="mediconnect.k8s.local"' >> ~/.zshrc
echo 'export KOPS_STATE_STORE="s3://mediconnect-kops-state-aak"' >> ~/.zshrc

# ─────────────────────────────────────────────────────────────
# STEP 8: Create Kubernetes Cluster (Kops)
# ─────────────────────────────────────────────────────────────
kops create cluster \
  --name="${CLUSTER_NAME}" \
  --state="${KOPS_STATE_STORE}" \
  --cloud=aws \
  --kubernetes-version=1.32.0 \
  --control-plane-count=3 \
  --control-plane-size=t3.medium \
  --control-plane-zones=eu-north-1a,eu-north-1b,eu-north-1c \
  --node-count=3 \
  --node-size=t3.medium \
  --zones=eu-north-1a,eu-north-1b,eu-north-1c \
  --topology=private \
  --networking=calico \
  --ssh-public-key=~/.ssh/mediconnect_nodes.pub \
  --encrypt-etcd-storage \
  --authorization=RBAC

# Review and apply
kops update cluster --name="${CLUSTER_NAME}" --yes --admin

# Wait for cluster (takes ~10-15 minutes)
kops validate cluster --wait=15m

# Confirm nodes are up
kubectl get nodes

# ─────────────────────────────────────────────────────────────
# STEP 9: Install cluster tooling
# ─────────────────────────────────────────────────────────────

# NGINX Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.replicaCount=2

# cert-manager (SSL certificates)
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true

# Sealed Secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.26.0/controller.yaml

# Wait for all to be ready
kubectl get pods -n ingress-nginx
kubectl get pods -n cert-manager
kubectl get pods -n kube-system | grep sealed

# ─────────────────────────────────────────────────────────────
# STEP 10: Get the Load Balancer hostname (to update Terraform)
# ─────────────────────────────────────────────────────────────
kubectl get service ingress-nginx-controller -n ingress-nginx

# Copy the EXTERNAL-IP / HOSTNAME value
# Then update terraform/environments/production/terraform.tfvars:
# ingress_lb_hostname = "YOUR_ELB_HOSTNAME_HERE"

# Apply Route53 DNS records
cd terraform/environments/production
terraform apply

echo ""
echo "✅ Phase 1 COMPLETE!"
echo "   Cluster: ${CLUSTER_NAME}"
echo "   State:   ${KOPS_STATE_STORE}"
echo "   Domains: mediconnect.salman-aak.com"
echo "            api.mediconnect.salman-aak.com"
echo "            ws.mediconnect.salman-aak.com"
echo ""
echo "📦 Next: Phase 2 — Django Backend API"
