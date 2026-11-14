# Moonfin REC 3.1 functional migration

- Official base commit: 5c5be56a02e2e2a0be5d06a6c485ff1172bfe270
- REC 3.0 custom ref: origin/moonfin-rec-3.0-final-20261104
- Shared ancestor: eb43b626f6f9239e1dd050e529de28702b08038c
- UI, My Media, layout, artwork placement, settings shell: official 3.1
- Functional merges are three-way with no automatic override on conflicts

## Applied cleanly
- build-windows.ps1
- lib/data/viewmodels/recordings_view_model.dart
- lib/playback/media3_playback_health.dart (new file)
- lib/playback/playback_profile_diagnostics.dart
- lib/playback/playback_quality_diagnostics.dart (new file)
- lib/preference/user_preferences.dart
- lib/ui/screens/livetv/live_tv_recordings_screen.dart
- lib/util/live_tv_recording.dart (new file)
- packages/server_core/lib/src/api/live_tv_api.dart
- packages/server_emby/lib/src/api/emby_live_tv_api.dart
- packages/server_jellyfin/lib/src/api/jellyfin_live_tv_api.dart
- packages/server_plex/lib/src/api/plex_live_tv_api.dart
- test/data/viewmodels/recording_delete_test.dart (new file)
- test/playback/media3_playback_health_test.dart (new file)
- test/playback/playback_quality_diagnostics_test.dart (new file)
- test/util/live_tv_recording_test.dart (new file)
- windows/runner/Runner.rc
- windows/runner/main.cpp
- lib/l10n/app_en.arb (36 REC strings)
- lib/l10n/app_it.arb (26 REC strings)

## Manual conflict resolution required
- **lib/playback/media3_player_backend.dart**: three-way content conflict
- **lib/playback/playback_info_sections.dart**: three-way content conflict
- **lib/ui/screens/livetv/live_tv_player_screen.dart**: three-way content conflict
- **lib/ui/screens/playback/video_player_screen.dart**: three-way content conflict
- **lib/ui/screens/settings/settings_side_panel.dart**: three-way content conflict

## Unchanged
