package org.moonfin.nativevideo

/** DTS decoding/bitstream paths must not opt in to tunneled A/V playback. */
internal object DtsTunnelingPolicy {
    fun isDtsCodec(codec: String?): Boolean {
        val value = codec?.trim()?.lowercase() ?: return false
        return value == "dts" || value == "dca" ||
            value.startsWith("dts-") || value.startsWith("dts_") ||
            value == "dtshd" || value == "dtsx"
    }

    fun isDtsMime(mime: String?): Boolean =
        mime?.trim()?.lowercase()?.startsWith("audio/vnd.dts") == true
}
