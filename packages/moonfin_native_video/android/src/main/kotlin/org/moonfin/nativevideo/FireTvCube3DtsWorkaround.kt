package org.moonfin.nativevideo

/**
 * Fire TV Cube 3 (AFTGAZL) can stall Media3 video when DTS is bitstreamed
 * through its AudioTrack, even while AC-3 playback is smooth.
 *
 * Only narrow automatic passthrough on this model. Manual mode remains an
 * explicit opt-in for users with known-good DTS receivers; other devices are
 * unchanged. The audio renderer can then decode DTS to PCM locally.
 */
internal object FireTvCube3DtsWorkaround {
    data class Policy(val mode: String, val codecs: Set<String>)

    fun apply(mode: String, codecs: Set<String>, deviceModel: String): Policy {
        if (deviceModel.trim().uppercase() != "AFTGAZL" || mode != "auto") {
            return Policy(mode, codecs)
        }
        return Policy(
            mode = "manual",
            codecs = AudioPassthroughPolicy.KNOWN_CODECS - setOf("dts", "dtshd"),
        )
    }
}
