#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_NAME="Moonfin"

resolve_flutter() {
  if [ -n "${FLUTTER_BIN:-}" ] && [ -x "$FLUTTER_BIN" ]; then
    printf '%s\n' "$FLUTTER_BIN"
    return 0
  fi
  if command -v flutter >/dev/null 2>&1; then
    command -v flutter
    return 0
  fi
  local candidates=(
    "$HOME/flutter/bin/flutter"
    "$HOME/Documents/flutter/bin/flutter"
    "$HOME/snap/flutter/common/flutter/bin/flutter"
  )
  local candidate
  for candidate in "${candidates[@]}"; do
    if [ -x "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  echo "Error: Flutter not found." >&2
  exit 1
}

FLUTTER="$(resolve_flutter)"

TV_VERSION=$(grep '^\s*android_tv_version:' "$REPO_ROOT/pubspec.yaml" | sed 's/.*android_tv_version:[[:space:]]*//' | tr -d '[:space:]')
TV_BUILD_NUMBER=$(grep '^\s*android_tv_build_number:' "$REPO_ROOT/pubspec.yaml" | sed 's/.*android_tv_build_number:[[:space:]]*//' | tr -d '[:space:]')

if [ -z "$TV_VERSION" ] || [ -z "$TV_BUILD_NUMBER" ]; then
  echo "Error: could not read android_tv_version / android_tv_build_number from pubspec.yaml" >&2
  exit 1
fi

TV_APK_SOURCE="$REPO_ROOT/build/app/outputs/flutter-apk/app-androidtv-release.apk"
TV_APK_OUTPUT="$REPO_ROOT/${APP_NAME}_AndroidTV_v${TV_VERSION}_REC.apk"

cd "$REPO_ROOT"

echo "Moonfin REC Android TV version: ${TV_VERSION} (${TV_BUILD_NUMBER})"
echo "Application ID suffix: .rec"

"$FLUTTER" clean
"$FLUTTER" pub get

export MOONFIN_TEST_ID_SUFFIX=".rec"

# Give the side-by-side TV test build a clear launcher name without changing
# another repository file permanently. This edit exists only on the GitHub runner.
sed -i 's/\$baseAppName Test/\$baseAppName REC/' "$REPO_ROOT/android/app/build.gradle.kts"

echo "Building ONLY Android TV REC APK..."
"$FLUTTER" build apk --release \
  --flavor androidTv \
  --build-name "$TV_VERSION" \
  --build-number "$TV_BUILD_NUMBER" \
  --dart-define=MOONFIN_FORCE_TV=true \
  --dart-define=DISTRIBUTION_CHANNEL=android_tv_apk

if [ ! -f "$TV_APK_SOURCE" ]; then
  echo "Error: TV APK not found at $TV_APK_SOURCE" >&2
  exit 1
fi

cp "$TV_APK_SOURCE" "$TV_APK_OUTPUT"

echo "DONE"
echo "APK: $TV_APK_OUTPUT"
