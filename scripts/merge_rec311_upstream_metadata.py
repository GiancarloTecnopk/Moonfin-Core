#!/usr/bin/env python3
"""Keep REC branding/TV metadata while importing new upstream 3.1.1 dependencies and i18n keys.

Invoke only during a three-way merge of the verified official tag (FETCH_HEAD).
Existing REC translations and dependency settings always win; this imports missing
upstream entries, including placeholder metadata, for every available locale.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def official_content(filename: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"FETCH_HEAD:{filename}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    return result.stdout.decode("utf-8-sig") if result.returncode == 0 else None


def import_missing_pubspec_dependencies() -> None:
    file = ROOT / "pubspec.yaml"
    local = file.read_text(encoding="utf-8")
    official = official_content("pubspec.yaml")
    if official is None:
        raise RuntimeError("Cannot load official Moonfin 3.1.1 pubspec")
    start_marker = "\ndependencies:\n"
    end_marker = "\ndev_dependencies:\n"
    if start_marker not in local or end_marker not in local:
        raise RuntimeError("Unexpected REC pubspec section layout")
    official_deps = official.split(start_marker, 1)[1].split(end_marker, 1)[0]
    local_deps = local.split(start_marker, 1)[1].split(end_marker, 1)[0]
    upstream = dict(re.findall(r"^  ([a-zA-Z_][a-zA-Z0-9_]*):[ \t]*([^\n]*)$", official_deps, re.M))
    current = set(re.findall(r"^  ([a-zA-Z_][a-zA-Z0-9_]*):", local_deps, re.M))
    missing = {name: value for name, value in upstream.items() if name not in current}
    if any(not value.strip() for value in missing.values()):
        raise RuntimeError(f"Complex upstream dependencies require explicit merge: {missing}")
    if missing:
        insertion = "".join(f"  {key}: {value}\n" for key, value in missing.items())
        before, after = local.split(end_marker, 1)
        file.write_text(before.rstrip("\n") + "\n" + insertion + end_marker + after, encoding="utf-8")
    print(f"Upstream dependencies imported: {list(missing)}")


def import_missing_translations() -> None:
    imported: dict[str, int] = {}
    for file in sorted((ROOT / "lib/l10n").glob("app_*.arb")):
        relative = file.relative_to(ROOT).as_posix()
        upstream_text = official_content(relative)
        if upstream_text is None:
            continue
        official = json.loads(upstream_text)
        original = file.read_text(encoding="utf-8-sig")
        current = json.loads(original)
        missing = [(key, value) for key, value in official.items() if key not in current]
        if not missing:
            continue
        body = original.rstrip()
        if not body.endswith("}"):
            raise RuntimeError(f"Cannot append translations in {relative}")
        body = body[:-1].rstrip()
        # Keep existing translations (including our REC strings), append only
        # official keys and @metadata absent from the local locale.
        separator = ",\n" if current else ""
        parts = []
        for key, value in missing:
            parts.append("  " + json.dumps(key, ensure_ascii=False) + ": " + json.dumps(value, ensure_ascii=False))
        updated = body + separator + ",\n".join(parts) + "\n}\n"
        parsed = json.loads(updated)
        if len(parsed) != len(current) + len(missing):
            raise RuntimeError(f"Localization key count mismatch: {relative}")
        file.write_text(updated, encoding="utf-8")
        imported[relative] = len(missing)
    print(f"Upstream localization entries imported: {imported}")
    en = json.loads((ROOT / "lib/l10n/app_en.arb").read_text(encoding="utf-8"))
    for key in ("remoteMediaNotificationTitle", "remoteActivityListening", "clickpadSeekingPausedOnly"):
        if key not in en:
            raise RuntimeError(f"Missing 3.1.1 localization: {key}")


if __name__ == "__main__":
    import_missing_pubspec_dependencies()
    import_missing_translations()
