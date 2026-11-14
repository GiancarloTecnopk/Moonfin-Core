#!/usr/bin/env python3
"""Port Moonfin REC 3.0 *functional* deltas into official Moonfin 3.1.

Run only on the isolated moonfin-rec-3.1-integration branch.
Do not replace 3.1 UI layouts or the 3.1 player wholesale.
A three-way merge reports conflicts instead of choosing an older implementation.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
REC = "origin/moonfin-rec-3.0-final-20261104"
REF = os.environ.get("GITHUB_REF_NAME", "")
EXPECTED_BRANCH = "moonfin-rec-3.1-integration-20261114"
if REF != EXPECTED_BRANCH:
    raise SystemExit(f"Refusing to migrate on branch {REF!r}; expected {EXPECTED_BRANCH!r}")

FILES = [
    "build-windows.ps1",
    "lib/data/viewmodels/recordings_view_model.dart",
    "lib/playback/media3_playback_health.dart",
    "lib/playback/media3_player_backend.dart",
    "lib/playback/playback_info_sections.dart",
    "lib/playback/playback_profile_diagnostics.dart",
    "lib/playback/playback_quality_diagnostics.dart",
    "lib/preference/user_preferences.dart",
    "lib/ui/screens/livetv/live_tv_player_screen.dart",
    "lib/ui/screens/livetv/live_tv_recordings_screen.dart",
    "lib/ui/screens/playback/video_player_screen.dart",
    "lib/ui/screens/settings/settings_side_panel.dart",
    "lib/util/live_tv_recording.dart",
    "packages/server_core/lib/src/api/live_tv_api.dart",
    "packages/server_emby/lib/src/api/emby_live_tv_api.dart",
    "packages/server_jellyfin/lib/src/api/jellyfin_live_tv_api.dart",
    "packages/server_plex/lib/src/api/plex_live_tv_api.dart",
    "test/data/viewmodels/recording_delete_test.dart",
    "test/playback/media3_playback_health_test.dart",
    "test/playback/playback_quality_diagnostics_test.dart",
    "test/util/live_tv_recording_test.dart",
    "windows/runner/Runner.rc",
    "windows/runner/main.cpp",
]
TRANSLATIONS = ["lib/l10n/app_en.arb", "lib/l10n/app_it.arb"]
SKIP_PORT_ALREADY_DONE = {
    "pubspec.yaml", "android/app/build.gradle.kts",
    "android/app/src/androidTv/AndroidManifest.xml",
    "packages/moonfin_native_video/android/src/main/kotlin/org/moonfin/nativevideo/Media3VideoView.kt",
    "packages/moonfin_native_video/android/src/main/kotlin/org/moonfin/nativevideo/HevcPacingPolicy.kt",
    "packages/moonfin_native_video/android/src/test/kotlin/org/moonfin/nativevideo/HevcPacingPolicyTest.kt",
}
assert not SKIP_PORT_ALREADY_DONE.intersection(FILES)
assert not set(TRANSLATIONS).intersection(FILES)

def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=ROOT, check=check, capture_output=True)

def show(ref: str, path: str) -> bytes | None:
    p = git("show", f"{ref}:{path}", check=False)
    return p.stdout if p.returncode == 0 else None

def write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

head = git("rev-parse", "HEAD").stdout.decode().strip()
baseline = git("merge-base", head, REC).stdout.decode().strip()
upstream_version = (ROOT / "pubspec.yaml").read_text()
if "android_tv_version: 3.1.0" not in upstream_version or "android_tv_build_number: 2000036" not in upstream_version:
    raise SystemExit("Wrong base version: aborting without touching files")

applied: list[str] = []
conflicts: list[tuple[str, str]] = []
untouched: list[str] = []
report_dir = ROOT / "rec31-merge-report"
report_dir.mkdir(exist_ok=True)

for relative in FILES:
    dest = ROOT / relative
    incoming = show(REC, relative)
    ancestor = show(baseline, relative)
    present = dest.read_bytes() if dest.is_file() else None
    if incoming is None:
        untouched.append(relative + " (not in REC)")
        continue
    if incoming == ancestor or incoming == present:
        untouched.append(relative)
        continue
    if ancestor is None:
        if present is None:
            write(dest, incoming)
            applied.append(relative + " (new file)")
        else:
            conflicts.append((relative, "new file also exists in 3.1"))
        continue
    if present is None:
        conflicts.append((relative, "deleted or renamed upstream in 3.1"))
        continue
    with tempfile.TemporaryDirectory(prefix="rec31-merge-") as tmp:
        t = Path(tmp)
        ours, base, theirs = [t / x for x in ("official31", "ancestor", "rec30")]
        write(ours, present); write(base, ancestor); write(theirs, incoming)
        merge = subprocess.run(
            ["git", "merge-file", "-p", "-L", "official_3.1", "-L", "merge_base", "-L", "REC_3.0",
             str(ours), str(base), str(theirs)],
            cwd=ROOT, capture_output=True
        )
        if merge.returncode == 0:
            if merge.stdout != present:
                write(dest, merge.stdout)
                applied.append(relative)
            else:
                untouched.append(relative)
        elif merge.returncode > 0:
            conflicts.append((relative, "three-way content conflict"))
            write(report_dir / (relative.replace("/", "__") + ".merge.txt"), merge.stdout)
        else:
            conflicts.append((relative, "merge-file failed: " + merge.stderr.decode(errors="replace")[:200]))

# Preserve the official 3.1 strings and only add REC-specific strings missing upstream.
# Modified existing strings are carried over only for the REC recording/EPG workflow,
# and only if upstream kept the original ancestor string.
REC_LABEL = re.compile(r"record|registr|epg|refresh|librar|delete|elimin", re.I)
for relative in TRANSLATIONS:
    present_path = ROOT / relative
    ancestor = show(baseline, relative)
    incoming = show(REC, relative)
    present = present_path.read_bytes() if present_path.exists() else None
    if ancestor is None or incoming is None or present is None:
        conflicts.append((relative, "missing localization source"))
        continue
    try:
        base = json.loads(ancestor)
        old = json.loads(incoming)
        new = json.loads(present)
    except Exception as e:
        conflicts.append((relative, f"localization JSON parse error: {e}"))
        continue
    fresh = []
    for key, value in old.items():
        if key not in base and key not in new:
            new[key] = value
            fresh.append(key)
        elif (key in base and key in new and value != base[key]
              and new[key] == base[key] and REC_LABEL.search(key)):
            new[key] = value
            fresh.append(key)
    if fresh:
        write(present_path, (json.dumps(new, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        applied.append(f"{relative} ({len(fresh)} REC strings)")
    else:
        untouched.append(relative)

lines = [
    "# Moonfin REC 3.1 functional migration",
    "",
    f"- Official base commit: {head}",
    f"- REC 3.0 custom ref: {REC}",
    f"- Shared ancestor: {baseline}",
    "- UI, My Media, layout, artwork placement, settings shell: official 3.1",
    "- Functional merges are three-way with no automatic override on conflicts",
    "",
    "## Applied cleanly",
    *[f"- {x}" for x in applied],
    "",
    "## Manual conflict resolution required",
    *([f"- **{p}**: {reason}" for p, reason in conflicts] or ["- None"]),
    "",
    "## Unchanged",
    *[f"- {x}" for x in untouched],
]
report_text = "\n".join(lines) + "\n"
write(report_dir / "README.md", report_text.encode())
print(report_text)
summary = os.environ.get("GITHUB_STEP_SUMMARY")
if summary:
    with open(summary, "a", encoding="utf-8") as f:
        f.write(report_text)
git("add", "--", *FILES, *TRANSLATIONS)
git("add", "--", str(report_dir.relative_to(ROOT)))
if git("diff", "--cached", "--quiet", check=False).returncode != 0:
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    git("commit", "-m", "port(rec31): merge REC functional changes into official 3.1 UI; document conflicts")
    git("push", "origin", f"HEAD:{EXPECTED_BRANCH}")
if conflicts:
    raise SystemExit(f"{len(conflicts)} paths need manual resolution; no release should be built")
print("Clean functional merge. Review source and run Android/Windows tests before a release.")
