#!/usr/bin/env python3
"""Apply Whol REC experiment over pinned Wholphin Jellyfin 12 source tree.

The original Wholphin player, HEVC, DTS and Dolby Vision handling is not
modified. Only Jellyfin DVR service, Live TV OSD, package identity and
null-safe DVR scheduling are changed.
"""
from pathlib import Path
import shutil
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: python scripts/apply_whol_rec.py /path/to/wholphin-upstream")

root = Path(sys.argv[1]).resolve()
repo = Path(__file__).resolve().parent.parent
overlay = repo / "whol_rec_overlay"

for source in sorted(overlay.rglob("*")):
    if not source.is_file():
        continue
    target = root / source.relative_to(overlay)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    print("Overlay:", target.relative_to(root))


def update(relative, anchor, replacement):
    p = root / relative
    s = p.read_text(encoding="utf-8")
    if s.count(anchor) != 1:
        raise RuntimeError("Expected exactly one occurrence of anchor in " + relative + ": " + anchor[:100])
    p.write_text(s.replace(anchor, replacement), encoding="utf-8")
    print("Patched:", relative)


page = "app/src/main/java/com/github/damontecres/wholphin/ui/playback/PlaybackPage.kt"
update(
    page,
    "import com.github.damontecres.wholphin.ui.playback.overlay.SkipSegmentButton",
    "import com.github.damontecres.wholphin.ui.playback.overlay.SkipSegmentButton\n"
    "import com.github.damontecres.wholphin.ui.playback.overlay.WholRecControls\n"
    "import org.jellyfin.sdk.model.api.BaseItemKind",
)
update(
    page,
    "            var subtitleStyleAppliedForHdr by remember",
    """            // Whol REC is strictly a Live TV overlay. Playback engine unchanged.
            state.currentPlayback?.item
                ?.takeIf { it.type == BaseItemKind.TV_CHANNEL }
                ?.let { liveChannel ->
                    WholRecControls(
                        channelId = liveChannel.id,
                        channelName = liveChannel.name ?: "Live TV",
                        controlsVisible = controllerViewState.controlsVisible,
                        modifier = Modifier
                            .align(Alignment.TopEnd)
                            .padding(top = 48.dp, end = 24.dp),
                    )
                }

            var subtitleStyleAppliedForHdr by remember""",
)

# Manual time-based DVR timers have no programInfo; avoid force-unwrapping
# when opening Wholphin's existing DVR schedule.
dvr = "app/src/main/java/com/github/damontecres/wholphin/ui/detail/livetv/DvrSchedule.kt"
update(
    dvr,
    "                            .map {\n                                BaseItem.from(\n                                    it.programInfo!!,\n                                    api,\n                                    true,\n                                )\n                            } // TODO this probably breaks for time based recordings",
    "                            .mapNotNull { timer ->\n"
    "                                timer.programInfo?.let { BaseItem.from(it, api, true) }\n"
    "                            } // Manual REC timers are tracked in Live TV OSD",
)

# Unique package: can coexist with upstream Wholphin and Moonfin REC.
gradle = "app/build.gradle.kts"
update(
    gradle,
    'applicationId = "com.github.damontecres.wholphin"',
    'applicationId = "com.github.damontecres.wholphin.wholrec"',
)
update(
    gradle,
    'versionName = gitDescribe.trim().removePrefix("v").ifBlank { "0.0.0" }',
    'versionName = "1.2.0-whol-rec-test1"',
)

res = "app/src/main/res/values/strings.xml"
update(res, '<string name="app_name" translatable="false">Wholphin</string>',
       '<string name="app_name" translatable="false">Wholphin REC Test</string>')
update(res, '<string name="app_name_long" translatable="false">Wholphin</string>',
       '<string name="app_name_long" translatable="false">Wholphin REC Test</string>')
print("Whol REC overlay successfully applied (Jellyfin DVR manual REC / STOP / TV OSD).")
