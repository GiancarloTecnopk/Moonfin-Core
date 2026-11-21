package com.github.damontecres.wholphin.services

import com.github.damontecres.wholphin.preferences.AppPreference
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class WholRecBitrateMigrationTest {
    @Test
    fun newPlaybackDefaultIs200() {
        assertEquals(200L * AppPreference.MEGA_BIT, AppPreference.DEFAULT_BITRATE)
        assertTrue(AppPreference.bitrateValues.contains(AppPreference.DEFAULT_BITRATE))
    }

    @Test
    fun upgradesOnlyStoredOldDefaultOnFirstRun() {
        val oldDefault = 100L * AppPreference.MEGA_BIT
        assertTrue(shouldUpgradeLegacyMaxBitrate(oldDefault, false))
        assertFalse(shouldUpgradeLegacyMaxBitrate(oldDefault, true))
    }

    @Test
    fun keepsOtherCustomBitratesAndZeroUntouched() {
        assertFalse(shouldUpgradeLegacyMaxBitrate(200L * AppPreference.MEGA_BIT, false))
        assertFalse(shouldUpgradeLegacyMaxBitrate(50L * AppPreference.MEGA_BIT, false))
        assertFalse(shouldUpgradeLegacyMaxBitrate(0, false))
    }
}
