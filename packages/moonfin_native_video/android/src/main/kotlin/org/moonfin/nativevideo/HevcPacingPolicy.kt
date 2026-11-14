package org.moonfin.nativevideo

/**
 * Scoped A/B experiment for HEVC playback on Fire TV / Amlogic devices.
 *
 * HEVC has a native Media3 release scheduler which already accounts for
 * codec timing, timestamps and display vsync. The custom one-vsync pacer
 * can introduce micro-pauses invisible to the dropped-frame counter.
 * Keep that pacer on every non-HEVC codec to minimize regressions.
 *
 * No change to bitrate, buffering, HDR metadata or decoder selection.
 */
internal object HevcPacingPolicy {
    fun useCustomVsyncPacing(mimeType: String?): Boolean =
        !mimeType.equals("video/hevc", ignoreCase = true)
}
