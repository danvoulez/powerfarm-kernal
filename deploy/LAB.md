# Powerfarm LAB — Mac mini deployment (one-time setup, ~15 min)

Compute lives in the lab. Edge is Cloudflare. Truth is Supabase Postgres.

## 1. Cloudflare Tunnel (once per machine)

```bash
# on the Mac mini (homebrew)
brew install cloudflared
cloudflared tunnel login                       # opens browser, pick powerfarm.app
cloudflared tunnel create powerfarm-lab        # prints TUNNEL_ID + credentials json
cloudflared tunnel route dns powerfarm-lab api.powerfarm.app
cloudflared tunnel route dns powerfarm-lab app.powerfarm.app   # when the SPA exists
```

Tunnel ingress (Cloudflare Zero Trust dashboard → Networks → Tunnels → powerfarm-lab → Public Hostnames):

| Public hostname        | Service                |
|------------------------|------------------------|
| `api.powerfarm.app`    | `http://pf-worker:8000`|
| `app.powerfarm.app`    | `http://pf-worker:8000`|  (temporary, until the SPA ships)

Copy the tunnel token: `cloudflared tunnel token powerfarm-lab`.

## 2. Environment (.env on the Mac mini, chmod 600, never in git)

```
DATABASE_URL=postgresql://postgres.<ref>:<password>@aws-0-eu-central-1.pooler.supabase.com:5432/postgres
GENESIS_ROOT_HASH=<from python -m genesis.ceremony>
GOOGLE_API_KEY=<gemini api key>
CLOUDFLARE_TUNNEL_TOKEN=<from step 1>
```

## 3. Run

```bash
docker compose --env-file .env up -d
docker compose ps        # pf-worker, pf-agent, cloudflared healthy
curl https://api.powerfarm.app/health
```

## 4. Deploys after this

GitHub Actions does it: merge to main → build images → SSH to the Mac mini →
`docker compose pull && up -d` → smoke test. Nothing by hand.

## Notes

- No inbound ports on the lab router. The tunnel is outbound-only.
- TLS is terminated at the Cloudflare edge; lab traffic stays on the docker network.
- The Mac mini never holds Supabase service-role keys except inside pf-worker env.
- RS256 JWKS verification means the lab can verify Powerfarm JWTs with public keys only.
