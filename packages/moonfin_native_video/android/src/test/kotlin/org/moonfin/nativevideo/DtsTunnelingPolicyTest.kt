package org.moonfin.nativevideo

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class DtsTunnelingPolicyTest {
    @Test fun recognizesDtsCoreAndExtensions() {
        listOf("dts", "DCA", "DTS-HD MA", "dts-hd", "dtshd", "dts_x", "dtsx").forEach {
            // DTS-HD MA variants passed as a title are handled by prefix.
            assertTrue("Expected DTS codec: $it", DtsTunnelingPolicy.isDtsCodec(it))
        }
    }

    @Test fun identifiesDtsMedia3Mimes() {
        listOf("audio/vnd.dts", "audio/vnd.dts.hd", "audio/vnd.dts.uhd").forEach {
            assertTrue(DtsTunnelingPolicy.isDtsMime(it))
        }
    }

    @Test fun preservesDolbyAndOtherAudioPaths() {
        listOf(null, "", "ac3", "eac3", "truehd", "aac", "flac", "opus").forEach {
            assertFalse(DtsTunnelingPolicy.isDtsCodec(it))
        }
        listOf(null, "audio/ac3", "audio/eac3", "audio/mp4a-latm").forEach {
            assertFalse(DtsTunnelingPolicy.isDtsMime(it))
        }
    }
}
