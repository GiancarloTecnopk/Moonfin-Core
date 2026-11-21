#!/usr/bin/env python3
"""Apply Whol REC experiment over pinned Wholphin Jellyfin 12 source tree.

The original Wholphin player, HEVC, DTS and Dolby Vision handling is not
modified. Only Jellyfin DVR service, Live TV OSD, package identity and
null-safe DVR scheduling are changed.
"""
from pathlib import Path
import os
import shutil
import subprocess
import sys

if len(sys.argv) != 2:
    raise SystemExit("Usage: python scripts/apply_whol_rec.py /path/to/wholphin-upstream")

root = Path(sys.argv[1]).resolve()
# GitHub Actions run numbers increment automatically on every build of this
# workflow, so every newly signed APK has a greater versionCode.
sequence = max(3, int(os.environ.get("GITHUB_RUN_NUMBER", "3")))
rec_version_code = 20001000 + sequence
rec_version_name = f"1.2.0-{sequence}-gwholrec"
repo = Path(__file__).resolve().parent.parent
overlay = repo / "whol_rec_overlay"

for source in sorted(overlay.rglob("*")):
    if not source.is_file() or source.name == 'README.md':
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


# Jellyfin 12 may return 401/403 on UserViews even after the account has
# authenticated. If fetching default Home settings throws, upstream leaves
# currentSettings == EMPTY, and HomePage displays a spinner forever.
# Always publish an identified non-empty settings object on recoverable API
# errors; HomeViewModel can then render its existing error screen instead of
# silently waiting in the pending state. This does not hide the 401 or reset
# credentials, and allows the user to see the real error.
update(
    "app/src/main/java/com/github/damontecres/wholphin/services/HomeSettingsService.kt",
    "            val resolvedSettings = settings ?: createDefault(user.id)\n"
    "            currentSettings.update { resolvedSettings }",
    """            val resolvedSettings =
                settings ?: try {
                    createDefault(user.id)
                } catch (ex: CancellationException) {
                    throw ex
                } catch (ex: Exception) {
                    Timber.e(ex, "Whol REC: default Home failed; surfacing library/API error instead of endless spinner")
                    HomePageResolvedSettings(user.id, HomePageSettingsSource.DEFAULT, emptyList())
                }
            currentSettings.update { resolvedSettings }""",
)

# Home startup bug in upstream Wholphin: it waits for the optional companion
# server plugin probe before starting to load the Home configuration. When the
# optional endpoint stalls, other tabs work but Home spins forever. Start Home
# settings immediately and probe the optional plugin independently.
update(
    "app/src/main/java/com/github/damontecres/wholphin/services/UserSwitchListener.kt",
    """                // Check if plugin is installed, then for home settings & seerr settings
                launchIO {""",
    """                // Home must not depend on the optional Wholphin plugin probe.
                launchIO {
                    homeSettingsService.loadCurrentSettings(user)
                }

                // Probe companion server plugin independently.
                launchIO {""",
)
update(
    "app/src/main/java/com/github/damontecres/wholphin/services/UserSwitchListener.kt",
    """                    launchIO {
                        // Check for home settings
                        homeSettingsService.loadCurrentSettings(user)
                    }

                    if (BuildConfig.DISCOVER_ENABLED) {""",
    """                    if (BuildConfig.DISCOVER_ENABLED) {""",
)

# HomeViewModel.init() wrongly treated a null dataLoadingJob as "already active":
# null?.isActive == false yields false. This prevented an initial/retry load
# even though the user and other tabs were fully authenticated.
update(
    "app/src/main/java/com/github/damontecres/wholphin/ui/main/HomeViewModel.kt",
    "if (dataLoadingJob?.isActive == false) {",
    "if (dataLoadingJob?.isActive != true) {",
)

# Raise only the negotiated streaming bitrate ceiling from 100 to 200 MiBit/s.
# Crucially, persistent DataStore on existing Fire TV installations contains
# the previous 100 value; changing the constant alone does not migrate it.
# A once-only targeted migration updates precisely that old value and leaves
# all user settings, codec selection and future manual choices untouched.
update(
    "app/src/main/java/com/github/damontecres/wholphin/preferences/AppPreference.kt",
    "const val DEFAULT_BITRATE = 100 * MEGA_BIT",
    "const val DEFAULT_BITRATE = 200 * MEGA_BIT",
)
prefs_service = "app/src/main/java/com/github/damontecres/wholphin/services/UserPreferencesService.kt"
update(
    prefs_service,
    "import androidx.datastore.core.DataStore",
    "import android.content.Context\n"
    "import androidx.datastore.core.DataStore\n"
    "import com.github.damontecres.wholphin.preferences.AppPreference\n"
    "import com.github.damontecres.wholphin.preferences.updatePlaybackPreferences\n"
    "import dagger.hilt.android.qualifiers.ApplicationContext\n"
    "import kotlinx.coroutines.sync.Mutex\n"
    "import kotlinx.coroutines.sync.withLock",
)
update(
    prefs_service,
    "    constructor(\n        private val serverRepository: ServerRepository,",
    "    constructor(\n"
    "        @param:ApplicationContext private val context: Context,\n"
    "        private val serverRepository: ServerRepository,",
)
update(
    prefs_service,
    "    ) {\n        val flow: Flow<UserPreferences> =",
    "    ) {\n"
    "        private val bitrateMigrationMutex = Mutex()\n\n"
    "        val flow: Flow<UserPreferences> =",
)
update(
    prefs_service,
    "        suspend fun getCurrent(): UserPreferences = flow.first()",
    """        suspend fun getCurrent(): UserPreferences {
            // Migrate before PlaybackViewModel.init() reads maxBitrate.
            bitrateMigrationMutex.withLock {
                val flags = context.getSharedPreferences("whol_rec_migrations", Context.MODE_PRIVATE)
                if (!flags.getBoolean("bitrate200_v1", false)) {
                    preferencesDataStore.updateData { saved ->
                        if (shouldUpgradeLegacyMaxBitrate(saved.playbackPreferences.maxBitrate, false)) {
                            saved.updatePlaybackPreferences {
                                maxBitrate = AppPreference.DEFAULT_BITRATE
                            }
                        } else {
                            saved
                        }
                    }
                    // Later manually selecting 100 must remain possible.
                    flags.edit().putBoolean("bitrate200_v1", true).apply()
                }
            }
            return flow.first()
        }""",
)

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

# Live TV EPG: retain the official per-program and series REC dialog, and add
# our management console for EPG refresh, NAS IPTV list refresh, library scan
# and manual DVR timers.
guide = "app/src/main/java/com/github/damontecres/wholphin/ui/detail/livetv/TvGuideGrid.kt"
update(
    guide,
    "import androidx.tv.material3.MaterialTheme",
    "import androidx.tv.material3.Button\nimport androidx.tv.material3.MaterialTheme",
)
update(
    guide,
    "    var showViewOptions by remember { mutableStateOf(false) }",
    "    var showViewOptions by remember { mutableStateOf(false) }\n"
    "    var showWholTools by remember { mutableStateOf(false) }",
)
update(
    guide,
    "                    TvGuideGridContent(",
    """                    if (focusedPosition.row < 1) {
                        Button(
                            onClick = { showWholTools = true },
                            modifier = Modifier.padding(start = tvGuideDimensions.channelWidth),
                        ) {
                            Text("REC • EPG / Liste / Librerie")
                        }
                    }
                    TvGuideGridContent(""",
)
update(
    guide,
    "    if (showViewOptions) {",
    """    if (showWholTools) {
        WholRecToolsDialog(onDismiss = { showWholTools = false })
    }
    if (showViewOptions) {""",
)

# Settings: also expose the same tools outside Live TV (accessible via remote
# even if the server has no tuner/EPG configured).
settings = "app/src/main/java/com/github/damontecres/wholphin/ui/preferences/PreferencesContent.kt"
update(
    settings,
    "import com.github.damontecres.wholphin.ui.components.ConfirmDialog",
    "import com.github.damontecres.wholphin.ui.detail.livetv.WholRecToolsDialog\n"
    "import com.github.damontecres.wholphin.ui.components.ConfirmDialog",
)
update(
    settings,
    "    var showVersionDialog by remember { mutableStateOf(false) }",
    "    var showVersionDialog by remember { mutableStateOf(false) }\n"
    "    var showWholRecTools by remember { mutableStateOf(false) }",
)
update(
    settings,
    "            ) {\n                serverVersionMessage?.let { message ->",
    """            ) {
                if (preferenceScreenOption == PreferenceScreenOption.BASIC) {
                    item {
                        ListItem(
                            selected = false,
                            onClick = { showWholRecTools = true },
                            headlineContent = { Text("Wholphin REC • TV e registrazioni") },
                            supportingContent = { Text("EPG, timer, liste IPTV NAS e librerie Jellyfin") },
                        )
                    }
                }
                serverVersionMessage?.let { message ->""",
)
update(
    settings,
    "    if (showLocaleChoiceDialog) {\n        LocaleChoiceDialog(",
    """    if (showWholRecTools) {
        WholRecToolsDialog(onDismiss = { showWholRecTools = false })
    }
    if (showLocaleChoiceDialog) {
        LocaleChoiceDialog(""",
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
    f'versionName = "{rec_version_name}"',
)

# Wholphin parses version names using git-describe strict syntax in
# UpdateViewModel.currentVersion. A label such as "1.2.0-whol-rec-test1"
# causes IllegalArgumentException as soon as Settings is opened.
update(
    gradle,
    'versionCode = gitTags.trim().lines().size',
    f'versionCode = {rec_version_code}',
)
# Never offer upstream Wholphin's (different-package) APK as a self-update.
update(gradle, 'setFeatureFlag(featureUpdate, true)',
       'setFeatureFlag(featureUpdate, false)')

# Guard against any future custom version string bringing back a settings crash.
update(
    "app/src/main/java/com/github/damontecres/wholphin/services/UpdateChecker.kt",
    'return Version.fromString(pkgInfo.versionName!!)',
    'return Version.tryFromString(pkgInfo.versionName) ?: Version(1, 2, 0)',
)

# The existing project secret is valid base64 with line wrapping. Wholphin's
# strict Base64.getDecoder() rejects embedded CR/LF; MIME decoder accepts
# wrapped base64 exactly as GNU base64 --decode did for Moonfin REC.
update(
    gradle,
    'Base64.getDecoder().decode(System.getenv("SIGNING_KEY"))',
    'Base64.getMimeDecoder().decode(System.getenv("SIGNING_KEY"))',
)

# Wholphin already provides persistent CI signing for release builds. Use the
# EXACT SAME CI signing configuration for debug REC packages. Without this
# change GitHub runners generate a new random ~/.android/debug.keystore each
# time, causing INSTALL_FAILED_UPDATE_INCOMPATIBLE on every update.
update(
    gradle,
    '        debug {\n            isMinifyEnabled = false',
    '        debug {\n            if (shouldSign.get()) {\n'
    '                signingConfig = signingConfigs.getByName("ci")\n'
    '            }\n            isMinifyEnabled = false',
)
update(
    gradle,
    '                storeFile = file("ci.keystore")',
    '                storeFile = file("ci.keystore")\n'
    '                storeType = System.getenv("KEY_STORE_TYPE").takeIf { !it.isNullOrBlank() } ?: "jks"',
)

res = "app/src/main/res/values/strings.xml"
update(res, '<string name="app_name" translatable="false">Wholphin</string>',
       '<string name="app_name" translatable="false">Wholphin REC Test</string>')
update(res, '<string name="app_name_long" translatable="false">Wholphin</string>',
       '<string name="app_name_long" translatable="false">Wholphin REC Test</string>')
# Generate distinct launcher and banner for Android TV and Fire TV.
# Preserve the source in this branch and re-render all density variants.
subprocess.run([sys.executable, str(repo / "scripts/generate_whol_rec_branding.py"), str(root)], check=True)

print(f"Whol REC build version: {rec_version_name} ({rec_version_code}); persistent CI signing for debug and release.")
print("Whol REC overlay successfully applied (Jellyfin DVR manual REC / STOP / TV OSD).")
