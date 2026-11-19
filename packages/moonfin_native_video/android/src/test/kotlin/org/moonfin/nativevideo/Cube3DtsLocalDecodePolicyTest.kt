package org.moonfin.nativevideo

import androidx.media3.common.Format
import androidx.media3.common.MimeTypes
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class Cube3DtsLocalDecodePolicyTest {
    @Test fun cube3VetoesDtsPassthroughEvenWhenAuto() {
        val policy = AudioPassthroughPolicy(
            mode = PassthroughMode.AUTO,
            allowedCodecs = emptySet(),
            forceLocalDtsDecode = true,
        )
        listOf(MimeTypes.AUDIO_DTS, MimeTypes.AUDIO_DTS_HD, MimeTypes.AUDIO_DTS_X).forEach { mime ->
            assertNull("DTS bitstream should decode locally: $mime",
                policy.sinkFormatFor(Format.Builder().setSampleMimeType(mime).build()))
        }
    }

    @Test fun dolbyPassthroughRemainsUnchanged() {
        val policy = AudioPassthroughPolicy(
            mode = PassthroughMode.AUTO,
            allowedCodecs = emptySet(),
            forceLocalDtsDecode = true,
        )
        listOf(MimeTypes.AUDIO_AC3, MimeTypes.AUDIO_E_AC3, MimeTypes.AUDIO_TRUEHD).forEach { mime ->
            assertEquals(mime, policy.sinkFormatFor(
                Format.Builder().setSampleMimeType(mime).build())?.sampleMimeType)
        }
    }

    @Test fun otherDevicesKeepAutoDtsPassthrough() {
        val policy = AudioPassthroughPolicy(PassthroughMode.AUTO, emptySet())
        assertEquals(MimeTypes.AUDIO_DTS, policy.sinkFormatFor(
            Format.Builder().setSampleMimeType(MimeTypes.AUDIO_DTS).build())?.sampleMimeType)
    }
}
