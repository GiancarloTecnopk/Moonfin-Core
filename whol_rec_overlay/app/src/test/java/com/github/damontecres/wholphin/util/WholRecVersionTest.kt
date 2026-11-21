package com.github.damontecres.wholphin.util

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Test

class WholRecVersionTest {
    @Test
    fun buildVersionAcceptedByWholphinSettingsVersionParser() {
        val version = Version.fromString("1.2.0-2-gwholrec")
        assertEquals(1, version.major)
        assertEquals(2, version.minor)
        assertEquals(0, version.patch)
        assertNotNull(Version.tryFromString("1.2.0-2-gwholrec"))
    }

    @Test
    fun originalCustomVersionWouldHaveCrashedSettings() {
        assertNull(Version.tryFromString("1.2.0-whol-rec-test1"))
    }
}
