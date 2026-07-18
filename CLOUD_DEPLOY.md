# Cloud Deployment — Alibaba Cloud ECS + Wildcard Subdomains

Multi-tenant deployment: each company gets its own subdomain.

```
fabrikayazilim.agent.fab.engineering
teknomuhendislik.agent.fab.engineering
           demo.agent.fab.engineering
```

All subdomains point to a single ECS instance. Data is isolated per company within the app.

---

## 1. Alibaba Cloud ECS

**Recommended spec (small team demo):**
- Region: Istanbul (me-east-1) or Singapore (ap-southeast-1)
- Instance: ecs.e-c1m2.large — 2 vCPU / 4 GB RAM
- OS: Ubuntu 22.04 LTS
- Disk: 40 GB (system) + 20 GB (data)
- Bandwidth: 5 Mbps (pay-by-traffic)

**Security Group rules:**
| Direction | Protocol | Port | Source |
|-----------|----------|------|--------|
| Inbound   | TCP      | 22   | Your IP |
| Inbound   | TCP      | 80   | 0.0.0.0/0 |
| Inbound   | TCP      | 443  | 0.0.0.0/0 |
| Outbound  | All      | All  | 0.0.0.0/0 |

---

## 2. DNS — Wildcard Record

In your DNS provider (Cloudflare recommended for free wildcard SSL):

```
Type   Name                     Value
A      agent.fab.engineering    <ECS_PUBLIC_IP>
A      *.agent.fab.engineering  <ECS_PUBLIC_IP>
```

**With Cloudflare:** set proxy status to "Proxied" (orange cloud) → free wildcard SSL, DDoS protection.

---

## 3. Server Setup

```bash
# SSH into ECS
ssh root@<ECS_PUBLIC_IP>

# Install Docker
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker

# Install Docker Compose plugin
apt install -y docker-compose-plugin

# Install Nginx
apt install -y nginx

# Clone the repo
git clone https://github.com/fab-agent/agentic-organization.git
cd agentic-organization

# Configure environment
cp backend/.env.example backend/.env
nano backend/.env
# Set: JWT_SECRET (64 random chars), QWEN_API_KEY, APP_URL
```

---

## 4. SSL Certificate

### Option A — Cloudflare (easiest)
If using Cloudflare proxy, SSL is automatic. No cert needed on the server.
Set Cloudflare SSL mode to "Full (strict)" after the first deploy.

### Option B — Let's Encrypt wildcard
```bash
apt install -y certbot python3-certbot-dns-cloudflare

# Create Cloudflare API token file
cat > /root/.cloudflare.ini << EOF
dns_cloudflare_api_token = <YOUR_CF_API_TOKEN>
EOF
chmod 600 /root/.cloudflare.ini

certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /root/.cloudflare.ini \
  -d agent.fab.engineering \
  -d "*.agent.fab.engineering"
```

---

## 5. Deploy

```bash
cd /root/agentic-organization

# Set your domain
export VITE_API_URL=https://agent.fab.engineering

# Build and start
docker compose -f docker-compose.yml -f docker-compose.cloud.yml up -d --build

# Verify
curl http://localhost:8000/health   # → {"status":"healthy"}
curl http://localhost:5173          # → HTML
```

---

## 6. Nginx Configuration

```bash
# Copy the wildcard config
cp nginx.cloud.conf.template /etc/nginx/sites-available/agent-fab

# Edit: replace ${DOMAIN}, ${SSL_CERT}, ${SSL_KEY} with actual values
# If using Cloudflare proxy, comment out the ssl_certificate lines
# and change listen 443 ssl to just listen 443

nano /etc/nginx/sites-available/agent-fab

# Add rate limit zone to /etc/nginx/nginx.conf inside http {}:
# limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

ln -s /etc/nginx/sites-available/agent-fab /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

---

## 7. Add a Company (tenant)

1. Open `https://agent.fab.engineering` → setup wizard runs
2. Enter founder info + company name
3. The company slug (e.g. `fabrika-yazilim`) is used as the subdomain
4. That company's users access: `https://fabrika-yazilim.agent.fab.engineering`
5. Login page shows company name and auto-selects the company after login

---

## 8. Verify Tenant Resolution

```bash
# Test the tenant API
curl https://agent.fab.engineering/tenant/resolve?slug=fabrika-yazilim
# → {"id":"...","name":"Fabrika Yazılım","slug":"fabrika-yazilim"}

# Test with Host header (simulates subdomain)
curl -H "Host: fabrika-yazilim.agent.fab.engineering" \
     https://agent.fab.engineering/tenant/resolve
# → same response
```

---

## Architecture

```
Internet
    │
    ▼
Cloudflare (wildcard SSL, DDoS, CDN)
    │  *.agent.fab.engineering → ECS IP
    ▼
Alibaba Cloud ECS
    │
    ├── Nginx (port 80/443)
    │     wildcard server_name *.agent.fab.engineering
    │     │
    │     ├── /auth, /companies, /tenant, /api/*  →  backend:8000 (FastAPI)
    │     └── /                                   →  frontend:5173 (SvelteKit)
    │
    ├── Docker: backend  (FastAPI + SQLite, port 127.0.0.1:8000)
    └── Docker: frontend (SvelteKit built, port 127.0.0.1:5173)

Tenant routing:
  fabrikayazilim.agent.fab.engineering
    → Nginx passes Host header to backend
    → Frontend reads hostname, calls GET /tenant/resolve?slug=fabrikayazilim
    → Login page shows "Fabrika Yazılım" branding
    → After login, auto-selects matching company
```
