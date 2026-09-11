# Deploying to DigitalOcean

Runbook for moving the National Statements Visualizations app from Render to a
DigitalOcean Droplet. It follows the Plan A / B / C cutover strategy agreed with
the Global CyberLaw Resource Project, documented in
`Plan_Migracion_Cutover_NatStateVis.md`.

The Render deployment keeps running untouched throughout. Nothing here affects
it until the DNS record changes in step 7.

---

## What changed in the code

The repository now runs on either provider from the same commit. Configuration
comes from environment variables instead of being hardcoded to Render.

| Area | Before | Now |
|---|---|---|
| Allowed hosts | `RENDER_EXTERNAL_HOSTNAME` only | `ALLOWED_HOSTS` env var, Render host still appended automatically |
| CSRF origins | Hardcoded `globalcyberlaw.onrender.com`, silently overriding the computed value | Derived from `ALLOWED_HOSTS`, or set explicitly |
| Login gate | Commented out in the middleware list | `REQUIRE_LOGIN` env var |
| Admin path | Always `/admin/` | `DJANGO_ADMIN_URL` env var |
| Database SSL | Always required | `DATABASE_SSL_REQUIRE`, off for a container on the private network |
| Secret key | Silently `None` if unset | Boot fails with an explanatory error |
| Health checks | None | `/healthz` and `/readyz` |
| TLS | Render-managed | Nginx with Let's Encrypt, TLS 1.2/1.3 only |
| Backups | None | Encrypted nightly dumps with retention |

Because Render injects `RENDER_EXTERNAL_HOSTNAME` itself, the Render service
needs no environment changes and keeps working unmodified.

---

## Prerequisites

- A Droplet: Ubuntu 24.04 LTS, NYC region, 2 GB RAM minimum. Plotly figure
  rendering is memory-hungry, and 1 GB will have Gunicorn workers killed.

  `s-1vcpu-2gb` is enough to launch on. Set `GUNICORN_WORKERS=2` for it, since
  figure rendering is CPU-bound and extra workers on one core only add memory
  pressure. The hardening script also adds swap, which DigitalOcean does not
  provide by default, so a spike degrades into slowness instead of the OOM
  killer terminating Postgres.

  If it turns out to need more, resize later in the DigitalOcean panel and
  choose the **CPU and RAM only** option. That one is reversible. The variant
  that also grows the disk cannot be undone.
- A domain you can edit DNS for.
- An SSH key uploaded to DigitalOcean.
- Render's External Database URL, from the Render dashboard.

---

## 1. Harden the Droplet

```bash
ssh root@<droplet-ip>
curl -fsSL https://raw.githubusercontent.com/marieleponti/globalcyberlawproject-ilit/main/ops/harden-droplet.sh -o harden.sh
less harden.sh     # read it before running it
bash harden.sh
```

Installs Docker, sets up a firewall allowing only 22/80/443, disables password
and root SSH, enables automatic security updates and fail2ban, and creates a
`deploy` user.

It pauses before changing SSH and asks you to confirm key login works in a
second terminal. Do actually check. Keep the DigitalOcean web console open as a
way back in.

Reboot afterwards to load the new kernel.

## 2. Clone and configure

```bash
ssh deploy@<droplet-ip>
sudo mkdir -p /opt && sudo chown deploy:deploy /opt
cd /opt
git clone https://github.com/marieleponti/globalcyberlawproject-ilit.git
cd globalcyberlawproject-ilit

cp .env.production.example .env.production
chmod 600 .env.production
nano .env.production
```

Every `CHANGE_ME` must be replaced. Generate the secrets on the Droplet:

```bash
python3 -c "import secrets,string; print(''.join(secrets.choice(string.ascii_letters+string.digits+'!@#\$%^&*(-_=+)') for _ in range(50)))"   # SECRET_KEY
openssl rand -base64 32    # POSTGRES_PASSWORD
openssl rand -base64 32    # BACKUP_PASSPHRASE
```

Do not reuse the Render `SECRET_KEY`. A new one invalidates existing sessions,
which means users log in again after the cutover. Their accounts and passwords
are unaffected.

Store `BACKUP_PASSPHRASE` somewhere other than this Droplet. A backup encrypted
with a key that only exists on the machine being backed up is not a backup.

Leave `SECURE_HSTS_SECONDS` and `HSTS_MAX_AGE` at `0` for now. Step 8 raises
them.

## 3. Test on a temporary subdomain

Do not point the production domain here yet. Point a throwaway name at the
Droplet instead, for example `test.nationalstatements.org`, and set `DOMAIN` and
`ALLOWED_HOSTS` in `.env.production` to that name.

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
docker compose -f docker-compose.prod.yml --env-file .env.production logs -f web
```

The web container runs migrations, collects static files, and runs Django's
deployment check before Gunicorn starts. A misconfiguration fails the boot here
rather than surfacing as a 500 later.

## 4. Issue the certificate

```bash
STAGING=1 ./ops/init-letsencrypt.sh    # rehearsal, not browser-trusted
./ops/init-letsencrypt.sh              # the real one
```

Use staging first. Let's Encrypt rate-limits failed issuance for the real
endpoint at five failures per hostname per hour, and a misconfigured webroot
burns through that quickly.

Renewal is automatic afterwards. The certbot container retries every 12 hours
and nginx reloads on the same cadence.

## 5. Validate everything

```bash
./ops/smoke-test.sh https://test.nationalstatements.org
# or, while the site is still login-gated:
USERNAME=admin PASSWORD=... ./ops/smoke-test.sh https://test.nationalstatements.org
```

Every route in the application is requested and the status code reported. Also
confirm by hand:

- TLS grade at https://www.ssllabs.com/ssltest/ (expect A or better)
- Login and logout
- The contact form actually delivers mail
- Each visualization renders, not just returns 200

Then prove the backup path works, because an untested backup is not a backup:

```bash
./ops/backup.sh
./ops/restore.sh backups/<the-file-just-written>
./ops/smoke-test.sh https://test.nationalstatements.org
```

## 6. Lower the DNS TTL

**Do this several days before the cutover, not on the day.**

Set the TTL on the production A record to 300 seconds. Resolvers around the
world cache the old value for as long as the old TTL says, so a record still
sitting at 24 hours will take a day to start honouring short TTLs. Lowering it
early is what makes both the cutover and the rollback take minutes.

The record itself still points at Render. Only the TTL changes.

## 7. Cut over

Pick a low-traffic window. The steps in order:

```bash
# 1. Stop writes on Render. Announce it, or choose a quiet hour.

# 2. Move the database. Run this as late as possible.
RENDER_DATABASE_URL='postgresql://...' ./ops/migrate-from-render.sh

# 3. Confirm accounts came across, on the test URL, before touching DNS.
./ops/smoke-test.sh https://test.nationalstatements.org
```

Then switch `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DOMAIN` and `WWW_DOMAIN`
in `.env.production` to the real domain, issue a certificate for it, and restart:

```bash
nano .env.production
./ops/init-letsencrypt.sh
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
```

Finally change the production A record to the Droplet IP and watch:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production logs -f web
watch -n 30 './ops/smoke-test.sh https://nationalstatements.org'
```

The database does not travel with `git pull`. It is a separate manual step, and
it is the one thing in this runbook that loses data if skipped or done too
early. Everything users do on Render between the dump and the DNS change is
lost, which is why step 2 runs as late as it does.

Leave the Render service **paused, not deleted**, for a few days.

## 8. After the cutover settles

Once TLS has been confirmed working on the real domain for a day or two, raise
HSTS in `.env.production`, one step at a time:

```
SECURE_HSTS_SECONDS=3600      # then, after a day, 31536000
HSTS_MAX_AGE=3600
```

Then restart nginx and web. Do not jump straight to a year. Browsers honour the
value they were last given until it expires, so a mistake made with a long
max-age cannot be withdrawn.

Schedule the nightly backup:

```bash
(crontab -l 2>/dev/null; echo "30 2 * * * cd /opt/globalcyberlawproject-ilit && ./ops/backup.sh >> /var/log/gclp-backup.log 2>&1") | crontab -
```

Enable DigitalOcean's weekly Droplet backups in the control panel. Those protect
against losing the Droplet; `ops/backup.sh` protects against losing the data.

## 9. Automatic deployment from GitHub

Every merge to `main` deploys to the Droplet. Set this up **after** the cutover
is stable, not before: while the branch is still being tested, `main` is what
Render serves.

On the Droplet:

```bash
cd /opt/globalcyberlawproject-ilit
./ops/setup-github-deploy.sh
```

It creates a dedicated SSH key and prints the four values to paste into GitHub
under Settings, Secrets and variables, Actions. Create an Environment named
`production` first and put them there, so you can require an approval before any
deploy reaches the live site.

The key it generates cannot be used for anything except deploying. Its
`authorized_keys` entry pins it to a forced command, so the Droplet runs
`ops/deploy.sh` no matter what the caller asks for. No shell, no file reads, no
port forwarding. Verify that yourself before trusting it:

```bash
ssh -i ~/.ssh/github_actions_deploy deploy@<droplet-ip> "cat /etc/passwd"
```

That must start a deployment, not print the file. If it prints the file, the
restriction is not in place and the key must not go into GitHub.

Two workflows run this:

| Workflow | Trigger | What it does |
|---|---|---|
| `.github/workflows/ci.yml` | pull requests, non-main branches | Django deploy checklist, missing-migration check, bandit, pip-audit, Docker build |
| `.github/workflows/deploy.yml` | push to `main`, manual | Runs CI first, then deploys over SSH and smoke-tests the live site |

A deploy that fails leaves the previous version running, and `ops/deploy.sh`
takes a database backup before it starts. The Droplet keeps its own log at
`ops/reports/deploy.log`, including deploys triggered from GitHub.

**Disconnect Render once you no longer need it as a fallback.** Otherwise a
merge to `main` deploys to two places at once.

## Making the site public

The site is login-gated until launch. On launch day:

```bash
sed -i 's/^REQUIRE_LOGIN=True/REQUIRE_LOGIN=False/' .env.production
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --no-deps web
```

No rebuild, no code change, a few seconds of downtime.

---

## Rollback

**If the cutover fails.** Point the DNS A record back at Render. With the TTL at
300 seconds from step 6, this propagates in minutes. Render still has its own
database, untouched by the migration, so it comes back exactly as it was. Then
diagnose the Droplet without time pressure.

**If a deployment fails.** `ops/deploy.sh` prints the previous commit and the
exact command to return to it, and takes a database backup before it starts.

**If a database import goes wrong.** `ops/migrate-from-render.sh` snapshots the
Droplet database before importing, and prints the restore command for it.

---

## Routine operations

| Task | Command |
|---|---|
| Deploy a change | Merge to `main`, or `./ops/deploy.sh` on the Droplet |
| Back up now | `./ops/backup.sh` |
| Restore a backup | `./ops/restore.sh backups/<file>` |
| Check all routes | `./ops/smoke-test.sh https://<domain>` |
| Security scan | `./ops/security-scan.sh` |
| Logs | `docker compose -f docker-compose.prod.yml --env-file .env.production logs -f web` |
| Django shell | `docker compose -f docker-compose.prod.yml --env-file .env.production exec web python manage.py shell` |
| Create a user | `... exec web python manage.py createsuperuser` |

---

## Architecture

```
                 Internet
                    |
          :80 / :443 (only open ports)
                    |
            +---------------+
            |     nginx     |  TLS 1.2/1.3, Let's Encrypt
            |   (frontend)  |  rate limits, security headers
            +---------------+
                    |
            +---------------+
            |      web      |  Gunicorn + Django + WhiteNoise
            | frontend +    |  non-root, health-checked
            |   backend     |
            +---------------+
                    |
            +---------------+
            |      db       |  Postgres 17, named volume
            |   (backend,   |  no published port, unreachable
            |   internal)   |  from nginx or the internet
            +---------------+
```

The `backend` network is marked internal, so the database has no route to or
from the internet. Only nginx publishes ports to the host.

---

## Security questionnaire status

Addressed by this configuration:

- TLS 1.2/1.3 only, modern cipher suites, HSTS, OCSP stapling
- Host firewall, key-only SSH, fail2ban, automatic security updates
- Non-root container user, `no-new-privileges`, network segmentation
- Encrypted backups with a defined retention period
- Vulnerability scanning via `ops/security-scan.sh` (pip-audit, bandit)
- Security headers and rate limiting on the credential-guessing surface

Still open, and not solvable in code:

- **Encryption at rest.** DigitalOcean encrypts Droplet storage at the platform
  level, which may answer the question as written. For a key you control, see
  `ops/setup-encrypted-volume.sh` and read its caveat: a LUKS volume must be
  unlocked by hand after every reboot, so the Droplet cannot return to service
  unattended.
- **Droplet exclusivity**, insurance, background checks, and a written security
  policy. These belong to the project lead, not the deployment.
- **From Temple**: the final domain and who provides it, institutional SSO
  versus native login, provisioning, SLA, and whether granular role-based access
  control is required.

See `Security_Questions_For_Vendors_TU_MARCADO.docx` and
`Preguntas_Para_Temple.docx` for the full list.
