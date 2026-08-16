import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read_json(path: str) -> dict[str, object]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_pack_versions_and_services_are_aligned() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    manifest = read_json("deploy/macos/manifest.json")
    version = (ROOT / "deploy/macos/VERSION").read_text(encoding="utf-8").strip()

    assert project["project"]["version"] == version
    assert manifest["version"] == version
    assert manifest["platform"] == "macos-launchd"
    assert set(manifest["services"]) == {
        "com.powerfarm.worker",
        "com.powerfarm.tunnel",
        "com.powerfarm.updater",
    }
    env_example = (ROOT / "deploy/macos/powerfarm.env.example").read_text(encoding="utf-8")
    assert "POWERFARM_BIND_HOST=127.0.0.1" in env_example
    assert manifest["mcp"] == {
        "protocol_version": "2026-07-28",
        "transport": "streamable-http",
        "path": "/mcp",
        "stateless": True,
    }
    assert "POWERFARM_AUTH_REQUIRED=true" in env_example


def test_auth_and_storage_contract_is_declarative() -> None:
    config = tomllib.loads((ROOT / "supabase/config.toml").read_text(encoding="utf-8"))
    clients = read_json("supabase/oauth-clients.json")
    manifest = read_json("deploy/macos/manifest.json")

    assert config["auth"]["passkey"]["enabled"] is True
    assert config["auth"]["webauthn"]["rp_id"] == "powerfarm.app"
    assert set(config["auth"]["webauthn"]["rp_origins"]) == {
        "https://powerfarm.app",
        "https://app.powerfarm.app",
    }
    assert config["auth"]["oauth_server"] == {
        "enabled": True,
        "authorization_url_path": "/oauth/consent",
        "allow_dynamic_registration": False,
    }
    assert clients == {
        "clients": [
            {
                "client_name": "Powerfarm CLI",
                "client_uri": "https://powerfarm.app",
                "redirect_uris": ["http://127.0.0.1:8484/oauth/callback"],
                "client_type": "public",
                "token_endpoint_auth_method": "none",
            }
        ]
    }
    assert set(manifest["supabase"]["storage_buckets"]) == {
        "powerfarm-ledger",
        "powerfarm-packages",
    }


def test_delivery_contract_is_protected_and_container_free() -> None:
    ruleset = read_json(".github/rulesets/main.json")
    checks_rule = next(rule for rule in ruleset["rules"] if rule["type"] == "required_status_checks")
    contexts = {
        item["context"] for item in checks_rule["parameters"]["required_status_checks"]
    }
    app = read_json("deploy/macos/github-app/manifest.json")

    assert contexts == {"quality", "migrations", "package"}
    assert app["hook_attributes"]["url"] == (
        "https://api.powerfarm.app/integrations/github/webhook"
    )
    assert app["default_permissions"] == {"actions": "read", "contents": "read"}
    assert not list(ROOT.glob("**/Dockerfile*"))
    assert not list(ROOT.glob("**/docker-compose*.yml"))
    assert not list(ROOT.glob("**/docker-compose*.yaml"))


def test_migration_history_is_sealed_and_ordered() -> None:
    migrations = sorted((ROOT / "supabase/migrations").glob("*.sql"))
    versions = [path.name.split("_", 1)[0] for path in migrations]

    assert (ROOT / "supabase/migrations/.sealed").is_file()
    # Sealed history only ever grows: a later migration may be added, but the
    # baseline and everything shipped after it may never leave. Immutability of
    # their *contents* is enforced against origin/main by
    # scripts/ci/check_migration_history.sh, which a count cannot express.
    assert migrations[0].name == "20260815060311_powerfarm_baseline.sql"
    assert len(migrations) >= 12
    assert len(versions) == len(set(versions))
    assert versions == sorted(versions)
