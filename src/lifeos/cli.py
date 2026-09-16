"""lifeos CLI: sync, auth, secret, doctor (spec §2)."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import typer

from lifeos import secrets as secrets_module
from lifeos.collectors import canvas, fixture
from lifeos.config import Config, load_config
from lifeos.doctor import run_doctor
from lifeos.engine import habits as habits_module
from lifeos.engine import routing, scoring, vault
from lifeos.engine.course_notes import update_course_grade
from lifeos.engine.snapshot import write_snapshot
from lifeos.engine.state import State, load_state, record_error, record_success, save_state
from lifeos.engine.sync_status import write_sync_status
from lifeos.logging_setup import get_logger
from lifeos.models import Item

app = typer.Typer(add_completion=False, help="LifeOS sync engine.")
secret_app = typer.Typer(add_completion=False, help="Manage secrets in Keychain.")
app.add_typer(secret_app, name="secret")

# Registered collectors. Phase 1+ adds learning_suite, gcal, icloud, gmail,
# outlook, slack, shopify here as they're built (docs/SPEC.md §5).
COLLECTORS = {
    "fixture": fixture.collect,
    "canvas": canvas.collect,
}

# Sources with grades that live on course notes rather than in 90 Sync/.
GRADE_COLLECTORS = {
    "canvas": canvas.collect_grades,
}


def _now(config: Config) -> datetime:
    return datetime.now(ZoneInfo(config.timezone))


def _process_item(item: Item, config: Config) -> Item:
    domain = routing.route(item, config)
    item = item.model_copy(update={"domain": domain})
    now = _now(config)
    item.score = scoring.score(item, now, config.weights, config.routing.vip)
    return item


@app.command()
def sync(
    source: str | None = typer.Option(None, "--source", help="Only sync this source."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Don't write to the vault; just show what would happen."),
) -> None:
    """Sync all sources by default. One failing source never stops the others."""
    config = load_config()
    logger = get_logger()
    now = _now(config)
    state = load_state()

    targets = [source] if source else list(COLLECTORS)
    unknown = [s for s in targets if s not in COLLECTORS]
    if unknown:
        typer.echo(f"Unknown source(s): {', '.join(unknown)}. Known: {', '.join(COLLECTORS)}")
        raise typer.Exit(1)

    if not dry_run:
        vault.reset_snoozed(config.vault_path, state, now.date().isoformat())

    for src in targets:
        try:
            items = [_process_item(i, config) for i in COLLECTORS[src](config)]
        except Exception as e:  # noqa: BLE001 - one failing source must not stop the others
            record_error(state, src, now, str(e))
            logger.error("source=%s failed: %s", src, e)
            typer.echo(f"[{src}] FAILED: {e}")
            continue

        if dry_run:
            typer.echo(f"[{src}] {len(items)} item(s) (dry run, nothing written):")
            for i in sorted(items, key=lambda x: -x.score)[:5]:
                due = i.due.isoformat() if i.due else "-"
                typer.echo(f"  {i.title!r:45s} domain={i.domain:8s} score={i.score:5.1f} due={due}")
        else:
            current_uids = {i.uid for i in items}
            for i in items:
                vault.merge_item(config.vault_path, i, state, now)
            removed = vault.reconcile_source(config.vault_path, src, current_uids, now)
            if removed:
                logger.info("source=%s reconciled=%d", src, len(removed))
            record_success(state, src, now)
            logger.info("source=%s items=%d", src, len(items))
            typer.echo(f"[{src}] synced {len(items)} item(s)")

        if src in GRADE_COLLECTORS:
            try:
                grades = GRADE_COLLECTORS[src](config)
            except Exception as e:  # noqa: BLE001 - grades failing must not stop items already synced
                logger.error("source=%s grades failed: %s", src, e)
                typer.echo(f"[{src}] grades FAILED: {e}")
                continue
            if dry_run:
                for g in grades[:5]:
                    typer.echo(f"  grade: {g['course']:20s} {g['grade']} ({g['letter']})")
            else:
                for g in grades:
                    update_course_grade(config.vault_path, g["course"], g["platform"], g["grade"], g["letter"], now)
                typer.echo(f"[{src}] updated {len(grades)} course grade(s)")

    if not dry_run:
        removed_events = vault.cleanup_ended_events(config.vault_path, now)
        removed_done = vault.prune_done(config.vault_path, state, now)
        if removed_events:
            logger.info("cleanup ended_events=%d", len(removed_events))
        if removed_done:
            logger.info("cleanup pruned_done=%d", len(removed_done))

        habit_list = habits_module.read_habits(config.vault_path)
        habits_module.ensure_daily_note(config.vault_path, now.date(), habit_list)
        habit_streaks = habits_module.compute_streaks(config.vault_path, now.date(), habit_list)

        write_sync_status(config.vault_path, state, now)
        write_snapshot(config.vault_path, state, now, habit_streaks)
        save_state(state)


@app.command()
def auth(
    source: str = typer.Argument(..., help="Source to authenticate, e.g. google, outlook."),
    account: str | None = typer.Option(None, "--account", help="Account name, for sources with multiple accounts."),
) -> None:
    """Interactive login flows. Phase 1+ adds real flows per source."""
    typer.echo(
        f"No interactive auth flow is implemented yet for '{source}' "
        f"(account={account or 'default'}). This lands with that source's collector."
    )


@secret_app.command("set")
def secret_set(key: str = typer.Argument(..., help="Keychain key, e.g. canvas_token.")) -> None:
    """Prompt for a value and store it in Keychain. Never echoes it."""
    secrets_module.set_secret(key)
    typer.echo(f"Stored '{key}' in Keychain (service: {secrets_module.SERVICE}).")


@app.command()
def doctor() -> None:
    """Config, auth status, vault paths, secret scan, last sync per source."""
    config = load_config()
    state = load_state()
    report = run_doctor(config, Path.cwd(), state)

    typer.echo(f"Config OK: {report.config_ok}")
    typer.echo(f"Vault path: {report.vault_path} (exists: {report.vault_exists})")

    typer.echo("\nExpected secrets:")
    if not report.expected_secrets:
        typer.echo("  (none configured yet)")
    for key, present in sorted(report.expected_secrets.items()):
        typer.echo(f"  [{'x' if present else ' '}] {key}")

    typer.echo("\nLast sync per source:")
    if not report.last_sync:
        typer.echo("  (no syncs recorded yet)")
    for src, ts in sorted(report.last_sync.items()):
        typer.echo(f"  {src}: {ts or 'never'}")

    typer.echo(f"\nSecret leak scan: {len(report.leak_hits)} hit(s)")
    for hit in report.leak_hits:
        typer.echo(f"  LEAK: {hit}")

    if not report.healthy:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
