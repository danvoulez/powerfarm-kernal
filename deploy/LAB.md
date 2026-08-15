# Powerfarm LAB - macOS launchd deployment

Compute lives directly on the Mac LAB. Edge ingress is a dedicated Cloudflare
Tunnel for `powerfarm.app`. Truth is Supabase Postgres.

No Docker, no Compose, no containers.

## Roles

| Surface | Responsibility |
|---|---|
| Mac LAB | Python venv, `pf-worker` launchd agent, local health endpoint |
| Cloudflare | Dedicated named tunnel, DNS routes for `powerfarm.app` hostnames |
| Supabase | Postgres migrations and managed platform services |

## Install

```bash
cp deploy/macos/powerfarm.env.example deploy/macos/powerfarm.env
$EDITOR deploy/macos/powerfarm.env
deploy/macos/install.sh --env deploy/macos/powerfarm.env
```

The install is designed to be idempotent:

- creates or reuses the LAB directory;
- creates or refreshes the Python environment;
- applies Supabase migrations through `psql`;
- creates or reuses the named Cloudflare Tunnel;
- writes a dedicated Cloudflare ingress config;
- installs/reloads the `com.powerfarm.worker` LaunchAgent;
- writes a versioned install receipt.

## Verify

```bash
deploy/macos/doctor.sh --env deploy/macos/powerfarm.env
deploy/macos/smoke.sh --env deploy/macos/powerfarm.env
```

## Update

```bash
deploy/macos/update.sh --env deploy/macos/powerfarm.env
```

`update.sh` reapplies the same converge steps as install and records a new
receipt. It is safe to run after every git pull.

## Uninstall

```bash
deploy/macos/uninstall.sh --env deploy/macos/powerfarm.env
```

By default uninstall removes launchd jobs and generated runtime config but keeps
data and receipts. Add `--purge` to remove the LAB runtime directory as well.

## Required local tools

- macOS with `launchctl`
- Python 3.12+
- `psql` for Supabase migrations
- `cloudflared` authenticated with Cloudflare for `powerfarm.app`

Cloudflare Tunnel's local-management flow creates a named tunnel, writes a
credentials JSON file, maps DNS with `cloudflared tunnel route dns`, and runs
the connector with `cloudflared tunnel --config ... run ...`.
