package org.moonfin.nativevideo

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class FireTvCube3DtsWorkaroundTest {
    @Test fun cube3AutoBlocksDtsAndDtsHdOnly() {
        val actual = FireTvCube3DtsWorkaround.apply("auto", emptySet(), "AFTGAZL")
        assertEquals("manual", actual.mode)
        assertFalse(actual.codecs.contains("dts"))
        assertFalse(actual.codecs.contains("dtshd"))
        assertTrue(actual.codecs.containsAll(setOf("ac3", "eac3", "truehd")))
    }

    @Test fun otherFireTvModelsKeepAutoPolicy() {
        assertEquals(
            FireTvCube3DtsWorkaround.Policy("auto", emptySet()),
            FireTvCube3DtsWorkaround.apply("auto", emptySet(), "AFTR"),
        )
    }

    @Test fun explicitManualDtsRemainsAvailable() {
        val expected = setOf("dts", "dtshd")
        assertEquals(
            FireTvCube3DtsWorkaround.Policy("manual", expected),
            FireTvCube3DtsWorkaround.apply("manual", expected, "AFTGAZL"),
        )
    }

    @Test fun disabledModeRemainsDisabled() {
        assertEquals(
            "disabled",
            FireTvCube3DtsWorkaround.apply("disabled", emptySet(), "AFTGAZL").mode,
        )
    }
}
