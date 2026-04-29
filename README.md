# Matrix / Synapse Self-Hosted Stack

A Docker Compose deployment of:

- **[Matrix Synapse](https://github.com/element-hq/synapse)** — Matrix homeserver
- **[coturn](https://github.com/coturn/coturn)** — TURN/STUN server for VoIP and video calls
- **[Keycloak](https://www.keycloak.org/)** — SSO / identity provider
- **[PostgreSQL 16](https://www.postgresql.org/)** — shared database for Synapse and Keycloak
- **[Nginx](https://nginx.org/)** — HTTPS reverse proxy
- **[Certbot](https://certbot.eff.org/)** — automatic Let's Encrypt TLS certificates

All domain names are configured in a single `.env` file and never hardcoded elsewhere.

---

## Prerequisites

- A Linux server with a **public IP address** running Ubuntu 22.04 or 24.04
- **Docker** and **Docker Compose v2** installed (see below)
- **DNS A records** pointing all four domains to your server's IP before running `init-certs.sh`
- Ports **80**, **443**, **3478**, **5349**, and **49152–49200/UDP** open in your firewall

---

## Installing Docker and Docker Compose on Ubuntu

> Skip this section if Docker is already installed. Run `docker compose version` to check.

### 1. Remove old versions (if any)

```bash
sudo apt remove -y docker docker-engine docker.io containerd runc
```

### 2. Add Docker's official apt repository

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

### 3. Install Docker Engine and the Compose plugin

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
                    docker-buildx-plugin docker-compose-plugin
```

### 4. Allow your user to run Docker without sudo

```bash
sudo usermod -aG docker $USER
newgrp docker          # apply the group change in the current shell
```

### 5. Verify the installation

```bash
docker version
docker compose version
```

Both commands should print version information without errors. Docker Compose v2 is
included as a plugin (`docker compose`) — note there is no hyphen, unlike the older
standalone `docker-compose` v1.

---

## Directory structure

```
.
├── .env.example                          # configuration template
├── docker-compose.yml
├── nginx/
│   ├── default.conf.template             # Nginx vhost config (uses envsubst)
│   └── entrypoint.sh                     # substitutes env vars; bootstraps HTTP-only mode if certs are missing
├── certbot/
│   └── entrypoint.sh                     # certificate renewal loop (every 12 h)
├── synapse/
│   ├── homeserver.yaml.template          # Synapse config (uses envsubst)
│   ├── log.config                        # Synapse logging
│   └── entrypoint.sh
├── coturn/
│   ├── turnserver.conf.template          # coturn config (uses envsubst)
│   └── entrypoint.sh
├── postgres/
│   └── init-databases.sh                 # creates synapse + keycloak databases on first boot
└── scripts/
    ├── init-certs.sh                     # one-time certificate initialisation (run before stack start)
    ├── backup.sh                         # snapshot databases, volumes, and .env to ./backups/
    └── uninstall.sh                      # tear down all containers, networks, and volumes
```

---

## Deployment

### 1. Clone and configure

```bash
git clone <this-repo> synapse-docker
cd synapse-docker
cp .env.example .env
```

Open `.env` and set every value — this is the **only file you need to edit**:

| Variable | Description |
|---|---|
| `MATRIX_DOMAIN` | Base domain for Matrix user IDs (`@user:example.com`) |
| `SYNAPSE_DOMAIN` | Public URL of the Synapse server (`matrix.example.com`) |
| `KEYCLOAK_DOMAIN` | Public URL of Keycloak (`auth.example.com`) |
| `TURN_DOMAIN` | Public URL of the TURN server (`turn.example.com`) |
| `SERVER_IP` | Public IP of this server (required for TURN NAT traversal) |
| `CERTBOT_EMAIL` | Email address for Let's Encrypt expiry notifications |
| `POSTGRES_PASSWORD` | PostgreSQL superuser password |
| `SYNAPSE_DB_PASSWORD` | Password for the `synapse` database user |
| `KEYCLOAK_DB_PASSWORD` | Password for the `keycloak` database user |
| `SYNAPSE_REGISTRATION_SECRET` | Secret for registering users via the admin API |
| `TURN_SECRET` | Shared secret between Synapse and coturn |
| `KEYCLOAK_ADMIN` | Keycloak admin console username |
| `KEYCLOAK_ADMIN_PASSWORD` | Keycloak admin console password |

> **Password rules:** avoid `$`, `'`, `\`, and `&` in passwords — these characters
> can break shell-based config substitution.

#### Generating strong passwords

Use `pwgen` to generate a secure random password for each secret field:

```bash
# Install pwgen if not already present
sudo apt install -y pwgen

# Generate a single 48-character password (no special chars to avoid substitution issues)
pwgen -s 48 1
```

Run it once per secret variable and paste each output into `.env`. For example:

```bash
POSTGRES_PASSWORD=$(pwgen -s 48 1)
SYNAPSE_DB_PASSWORD=$(pwgen -s 48 1)
KEYCLOAK_DB_PASSWORD=$(pwgen -s 48 1)
SYNAPSE_REGISTRATION_SECRET=$(pwgen -s 48 1)
TURN_SECRET=$(pwgen -s 48 1)
KEYCLOAK_ADMIN_PASSWORD=$(pwgen -s 48 1)

# Print them all to copy into .env
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
echo "SYNAPSE_DB_PASSWORD=$SYNAPSE_DB_PASSWORD"
echo "KEYCLOAK_DB_PASSWORD=$KEYCLOAK_DB_PASSWORD"
echo "SYNAPSE_REGISTRATION_SECRET=$SYNAPSE_REGISTRATION_SECRET"
echo "TURN_SECRET=$TURN_SECRET"
echo "KEYCLOAK_ADMIN_PASSWORD=$KEYCLOAK_ADMIN_PASSWORD"
```

#### MATRIX_DOMAIN vs SYNAPSE_DOMAIN

| Goal | Setting |
|---|---|
| User IDs like `@user:matrix.example.com` | Set both to the same value |
| User IDs like `@user:example.com` (delegation) | `MATRIX_DOMAIN=example.com`, `SYNAPSE_DOMAIN=matrix.example.com` |

When they differ, Nginx serves `/.well-known/matrix/` on `MATRIX_DOMAIN` to delegate
federation to `SYNAPSE_DOMAIN`.

---

### 2. Point DNS

Create an **A record** for your main domain and **CNAME records** for the subdomains:

```
example.com         A      <SERVER_IP>
matrix.example.com  CNAME  example.com
auth.example.com    CNAME  example.com
turn.example.com    CNAME  example.com
```

> If `MATRIX_DOMAIN` and `SYNAPSE_DOMAIN` are the same value, the A record is for
> that domain and the remaining subdomains point to it via CNAME.

Wait for DNS propagation before continuing.

---

### 3. Obtain TLS certificates (one-time)

This script uses certbot in **standalone mode** (no Nginx needed yet) to obtain a single
multi-SAN certificate covering all your domains. The certificate is stored in the
`certbot-certs` Docker volume under `live/<MATRIX_DOMAIN>/`.

```bash
bash scripts/init-certs.sh
```

Port 80 must be free on the host when this runs.

> **Note:** If you start the stack before running `init-certs.sh`, Nginx will
> automatically enter an HTTP-only bootstrap mode and print a waiting message in its
> logs. It will switch to HTTPS as soon as the certificates appear in the volume.

---

### 4. Start the stack

```bash
docker compose up -d
```

Services start in dependency order. Keycloak and Synapse take ~30–60 seconds on first
boot while initialising their databases.

Check that everything is healthy:

```bash
docker compose ps
docker compose logs -f   # Ctrl-C to exit
```

---

### 5. Create the first Matrix user

```bash
docker compose exec synapse register_new_matrix_user \
  -c /data/homeserver.yaml \
  -u <username> -p <password> --admin \
  http://localhost:8008
```

---

## Maintenance

### Certificate renewal

Certbot automatically attempts renewal every 12 hours using the **webroot** method
(Nginx serves the ACME challenge files). After a successful renewal, reload Nginx to
apply the new certificate:

```bash
docker compose exec nginx nginx -s reload
```

To automate the reload, add a cron job on the host:

```cron
0 3 * * * docker compose -f /path/to/synapse-docker/docker-compose.yml exec -T nginx nginx -s reload
```

### Update all images

```bash
docker compose pull
docker compose up -d
```

### View logs for a specific service

```bash
docker compose logs -f synapse
docker compose logs -f keycloak
docker compose logs -f nginx
docker compose logs -f certbot
```

### Backup

Run the backup script to snapshot all persistent state into a timestamped directory
under `./backups/`:

```bash
bash scripts/backup.sh
```

Each backup directory contains:

| File | Contents |
|---|---|
| `postgres.sql` | Full logical dump of all databases (Synapse + Keycloak) |
| `synapse-data.tar.gz` | Synapse signing key and media store |
| `certbot-certs.tar.gz` | TLS certificates and account keys |
| `.env` | All secrets and domain configuration |

The stack must be running when the script is executed (it needs the postgres container
to produce the SQL dump).

### Uninstall

To completely remove the stack including all data:

```bash
bash scripts/uninstall.sh
```

This stops all containers and deletes every named volume (databases, media store,
certificates). The action is irreversible — you will be prompted to confirm.

---

## Keycloak SSO integration with Synapse

### 1. Create the Matrix realm

1. Log in to `https://<KEYCLOAK_DOMAIN>` with your admin credentials.
2. Click **Create realm** and set the realm name to `matrix`.

### 2. Create the Synapse OIDC client

Inside the `matrix` realm, go to **Clients → Create client** and fill in the following,
then click **Save**:

| Setting | Value |
|---|---|
| Client ID | `synapse` |
| Client Type | `OpenID Connect` |
| Client authentication | On |
| Root URL | `https://<SYNAPSE_DOMAIN>` |
| Valid Redirect URIs | `https://<SYNAPSE_DOMAIN>/_synapse/client/oidc/callback` |

After saving, open the client's **Settings** tab, scroll to the **Logout settings** section, and update:

| Setting | Value |
|---|---|
| Front channel logout | Off |
| Backchannel logout URL | `https://<SYNAPSE_DOMAIN>/_synapse/client/oidc/backchannel_logout` |
| Backchannel logout session required | On |

Save again, then copy the **client secret** from the **Credentials** tab.

### 3. Configure Synapse

Set `KEYCLOAK_CLIENT_SECRET` in your `.env` file to the client secret you copied:

```bash
KEYCLOAK_CLIENT_SECRET=<paste-secret-here>
```

Then restart Synapse to apply the change:

```bash
docker compose restart synapse
```

---

## Architecture overview

```
Internet
   │
   ├─ :80  ──► Nginx ──► certbot webroot (ACME challenges)
   │                 └──► redirect to HTTPS
   │
   ├─ :443 ──► Nginx ──► Synapse  :8008  (Matrix client + federation)
   │                └──► Keycloak :8080  (SSO)
   │
   ├─ :3478 ─► coturn  (TURN/STUN plaintext)
   └─ :5349 ─► coturn  (TURN/STUN TLS)

Internal network (Docker bridge):
  Synapse ──► PostgreSQL (database: synapse)
  Keycloak ─► PostgreSQL (database: keycloak)
  coturn  ──► certbot-certs volume (TLS cert)
  Nginx   ──► certbot-certs volume (TLS cert)
             certbot-webroot volume (ACME challenge files)
```

TLS is terminated at Nginx for web traffic. coturn handles its own TLS directly using
the shared Let's Encrypt certificate — a multi-SAN cert covering all configured domains,
stored under `live/<MATRIX_DOMAIN>/` in the `certbot-certs` volume.

---

## Ports reference

| Port | Protocol | Service | Purpose |
|---|---|---|---|
| 80 | TCP | Nginx | HTTP → HTTPS redirect + ACME challenges |
| 443 | TCP | Nginx | HTTPS (Synapse, Keycloak) |
| 3478 | UDP/TCP | coturn | TURN/STUN |
| 5349 | UDP/TCP | coturn | TURN/STUN over TLS |
| 49152–49200 | UDP | coturn | TURN relay ports |
