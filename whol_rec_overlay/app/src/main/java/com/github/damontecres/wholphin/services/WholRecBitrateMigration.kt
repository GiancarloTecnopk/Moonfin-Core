package com.github.damontecres.wholphin.services

import com.github.damontecres.wholphin.preferences.AppPreference

/**
 * One-time migration for clients that persisted the former default (100 MiBit/s).
 * Other saved values and subsequent user changes must not be touched.
 */
internal fun shouldUpgradeLegacyMaxBitrate(
    saved: Long,
    migrationCompleted: Boolean,
): Boolean = !migrationCompleted && saved == 100L * AppPreference.MEGA_BIT
