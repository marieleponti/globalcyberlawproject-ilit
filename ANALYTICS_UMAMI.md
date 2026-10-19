# Umami web analytics

Self-hosted, cookie-free visitor statistics for the Django site and the EB site,
with a Google-Analytics-style dashboard that can be shared with the client.

Everything here is **off by default**. Merging the branch that added it changes
nothing on the running sites: the Umami containers sit behind the `analytics`
compose profile, the nginx block lives in an `.example` file, and the tracking
tag renders only once a website ID is configured.

What it adds:

| Piece | Where |
|---|---|
| `umami` + `umami_db` services (own Postgres, 512 MB cap) | `docker-compose.prod.yml`, profile `analytics` |
| nginx proxy for the stats domain | `nginx/umami-site.conf.template.example` |
| Tracking tag in the Django pages | `core/base.html`, fed by `UMAMI_SCRIPT_URL` / `UMAMI_WEBSITE_ID` |

## 1. DNS

Create an `A` record for the stats domain (for example
`stats.globalcyberlawproject.org`) pointing at the Droplet. If the zone is on
Cloudflare, leave it **DNS only (grey cloud)** while the certificate is issued.

## 2. Secrets

On the Droplet, add to `.env.production` (hex, not base64: the password is part
of a URL):

```
UMAMI_DOMAIN=stats.globalcyberlawproject.org
UMAMI_DB_PASSWORD=<openssl rand -hex 32>
UMAMI_APP_SECRET=<openssl rand -hex 32>
```

## 3. Switch it on

The order matters because nginx is shared: a template that names a missing
certificate stops nginx for every site on it.

```bash
cd /opt/globalcyberlawproject-ilit
PLACEHOLDER_ONLY=1 ./ops/issue-cert.sh stats.globalcyberlawproject.org
cp nginx/umami-site.conf.template.example nginx/templates/umami-site.conf.template

docker compose -f docker-compose.prod.yml --env-file .env.production --profile analytics up -d umami
docker compose -f docker-compose.prod.yml --env-file .env.production exec nginx nginx -t
docker compose -f docker-compose.prod.yml --env-file .env.production up -d nginx

STAGING=1 ./ops/issue-cert.sh stats.globalcyberlawproject.org   # rehearsal
FORCE=1   ./ops/issue-cert.sh stats.globalcyberlawproject.org   # the real one
```

Always pass `--env-file .env.production`; without it compose renders blank
passwords and domains.

## 4. First login (do this immediately)

Open `https://<stats domain>` and sign in with the **default** account
`admin` / `umami`. **Change that password at once**: the login page is public.

Then:

1. *Settings → Websites → Add website*, one per site (the ILIT and the EB
   frontend). Each gets a **website ID**.
2. To give the client access: *Settings → Users → Create*, role **View only**.
   They get a dashboard with visitors, pages, referrers, countries and devices,
   and no way to change anything. A per-website public share link is also
   available under the website's settings.

## 5. Tracking tag

**Django site (ILIT):** add to `.env.production`, then
`docker compose ... up -d --no-deps web`:

```
UMAMI_SCRIPT_URL=https://stats.globalcyberlawproject.org/script.js
UMAMI_WEBSITE_ID=<the ILIT website ID>
```

**EB site (Vue frontend, separate repository):** add to `index.html`'s `<head>`
in `vite-eb-site-api`, and redeploy it:

```html
<script defer src="https://stats.globalcyberlawproject.org/script.js"
        data-website-id="<the EB website ID>"></script>
```

## Notes

- **Backups.** `ops/backup.sh` covers only the application database. Umami's
  data is in the `umami_db_data` volume; dump it with
  `docker compose -f docker-compose.prod.yml --env-file .env.production exec -T umami_db pg_dump -U umami umami > umami.sql`.
- **Upgrades.** The image tag is rolling (`postgresql-latest`). Pin it once the
  version in use is known, and take the dump above before changing it.
- **Counting.** Umami counts people's page views, not bots, which is why its
  numbers will be far lower than the nginx logs. Both are right; they measure
  different things.
- **Off switch.** Remove the tag settings and recreate `web`, delete
  `nginx/templates/umami-site.conf.template` and recreate nginx, then
  `docker compose ... --profile analytics stop umami umami_db`.
