bool moonfinRecUsesNativeVideoSurface({
  required bool platformUsesNativeSurface,
  required bool forceTextureSurface,
}) => platformUsesNativeSurface && !forceTextureSurface;

bool moonfinRecHardwareDecodeEnabled({
  required bool preferenceEnabled,
  required bool forceSoftwareDecode,
}) => preferenceEnabled && !forceSoftwareDecode;
