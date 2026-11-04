package org.moonfin.nativevideo

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class HevcPacingPolicyTest {
    @Test fun bypassesPacerForHevcMainAndMain10() {
        assertFalse(HevcPacingPolicy.useCustomVsyncPacing("video/hevc"))
        assertFalse(HevcPacingPolicy.useCustomVsyncPacing("VIDEO/HEVC"))
    }

    @Test fun retainsPacerForUnrelatedCodecs() {
        assertTrue(HevcPacingPolicy.useCustomVsyncPacing("video/avc"))
        assertTrue(HevcPacingPolicy.useCustomVsyncPacing("video/av01"))
        assertTrue(HevcPacingPolicy.useCustomVsyncPacing(null))
    }
}
