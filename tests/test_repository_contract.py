from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_migration_history_is_sealed_and_ordered() -> None:
    migrations = sorted((ROOT / "supabase/migrations").glob("*.sql"))
    versions = [path.name.split("_", 1)[0] for path in migrations]

    assert (ROOT / "supabase/migrations/.sealed").is_file()
    assert migrations[0].name == "20260815060311_powerfarm_baseline.sql"
    assert len(migrations) >= 12
    assert len(versions) == len(set(versions))
    assert versions == sorted(versions)


def test_repository_has_no_machine_deployment_or_disabled_modules() -> None:
    assert not (ROOT / "deploy").exists()
    assert not (ROOT / "worker").exists()
    assert not (ROOT / "protocol/mcp/tasks.py").exists()
