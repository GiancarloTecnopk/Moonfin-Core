#!/usr/bin/env python3
"""Check TV launcher intent filters before signing a Moonfin REC Android TV APK."""
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent.parent
android = "{http://schemas.android.com/apk/res/android}"
main = ET.parse(root / "android/app/src/main/AndroidManifest.xml").getroot()
tv = ET.parse(root / "android/app/src/androidTv/AndroidManifest.xml").getroot()

def activity(manifest):
    app = manifest.find("application")
    assert app is not None, "missing application element"
    result = [x for x in app.findall("activity") if x.get(android + "name") == ".MainActivity"]
    assert len(result) == 1, "expected exactly one MainActivity per manifest"
    return app, result[0]

def categories(act):
    for filt in act.findall("intent-filter"):
        actions = [x.get(android + "name") for x in filt.findall("action")]
        cats = [x.get(android + "name") for x in filt.findall("category")]
        if "android.intent.action.MAIN" in actions:
            yield cats

main_app, main_act = activity(main)
tv_app, tv_act = activity(tv)
main_filters = list(categories(main_act))
tv_filters = list(categories(tv_act))
leanback = "android.intent.category.LEANBACK_LAUNCHER"
launcher = "android.intent.category.LAUNCHER"

assert sum(leanback in x for x in main_filters) == 0, "common manifest duplicates TV launch activity"
assert sum(launcher in x for x in main_filters) == 1, "common manifest needs exactly one normal launcher"
assert sum(leanback in x for x in tv_filters) == 1, "TV manifest needs exactly one Leanback launch intent"
assert sum(launcher in x for x in tv_filters) == 0, "TV manifest must not duplicate normal launcher"

for node, kind in ((tv_app, "application"), (tv_act, "MainActivity")):
    assert node.get(android + "icon") == "@drawable/moonfin_rec_launcher", kind + " missing REC icon"
    assert node.get(android + "banner") == "@drawable/moonfin_tv_banner", kind + " missing TV banner"

assert main_act.get(android + "exported") == "true", "MainActivity must be exported"
assert tv_act.get(android + "label") == "${appName}", "TV app label should be linked to REC flavor"
assert (root / "assets/branding/moonfin_rec_icon_256.png").exists(), "REC icon source missing"

print("PASS: one MAIN/LAUNCHER filter + one MAIN/LEANBACK_LAUNCHER filter; TV icon, banner, and exported MainActivity are defined")
