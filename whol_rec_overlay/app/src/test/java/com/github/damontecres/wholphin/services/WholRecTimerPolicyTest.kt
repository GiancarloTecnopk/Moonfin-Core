package com.github.damontecres.wholphin.services

import org.jellyfin.sdk.model.api.SeriesTimerInfoDto
import org.jellyfin.sdk.model.api.TimerInfoDto
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Assert.assertThrows
import org.junit.Test
import java.time.LocalDateTime
import java.time.ZoneOffset
import java.util.UUID

class WholRecTimerPolicyTest {
    private val channel = UUID.randomUUID()
    private val now = LocalDateTime.now(ZoneOffset.UTC)

    @Test
    fun activeManualTimerOnChannelIsSelected() {
        val timers = listOf(
            TimerInfoDto(
                id = "scheduled",
                channelId = channel,
                name = "Scheduled news",
                startDate = now.minusMinutes(1),
                endDate = now.plusHours(1),
            ),
            TimerInfoDto(
                id = "manual",
                channelId = channel,
                name = "Whol REC - Channel",
                startDate = now.minusMinutes(1),
                endDate = now.plusHours(1),
            ),
        )
        assertEquals("manual", selectActiveWholRecTimer(timers, channel, now)?.id)
    }

    @Test
    fun otherChannelsAndFinishedTimersAreNotTouched() {
        val timers = listOf(
            TimerInfoDto(
                id = "other",
                channelId = UUID.randomUUID(),
                name = "Whol REC - Other",
                startDate = now.minusMinutes(2),
                endDate = now.plusHours(1),
            ),
            TimerInfoDto(
                id = "finished",
                channelId = channel,
                name = "Whol REC - Channel",
                startDate = now.minusHours(2),
                endDate = now.minusMinutes(1),
            ),
        )
        assertNull(selectActiveWholRecTimer(timers, channel, now))
    }
    @Test
    fun manualRecUsesServerDvrServiceAndNeverRequiresEpg() {
        val defaults = SeriesTimerInfoDto(
            serviceName = "Emby",
            serverId = "nas-jellyfin",
            priority = 5,
        )
        val timer = createManualTimerFromDefaults(defaults, channel, "Test Channel", 30, now)
        assertEquals("Emby", timer.serviceName)
        assertEquals("nas-jellyfin", timer.serverId)
        assertEquals(channel, timer.channelId)
        assertEquals(5, timer.priority)
        assertEquals("Whol REC - Test Channel", timer.name)
        assertNull(timer.programId)
        assertNull(timer.externalProgramId)
        assertEquals(now.minusSeconds(5), timer.startDate)
        assertEquals(now.plusMinutes(30), timer.endDate)
        assertEquals(0, timer.prePaddingSeconds)
        assertEquals(0, timer.postPaddingSeconds)
    }

    @Test
    fun missingDvrServiceStopsLocallyBeforeHttp500() {
        val ex = assertThrows(IllegalStateException::class.java) {
            createManualTimerFromDefaults(
                SeriesTimerInfoDto(serviceName = null), channel, "Test Channel", 30, now
            )
        }
        assertTrue(ex.message.orEmpty().contains("ServiceName"))
    }

    @Test
    fun manualTimerDurationLimitsPreventInvalidSchedules() {
        val defaults = SeriesTimerInfoDto(serviceName = "Emby")
        for (duration in listOf(-1, 0, 481)) {
            assertThrows(IllegalArgumentException::class.java) {
                createManualTimerFromDefaults(defaults, channel, "Test Channel", duration, now)
            }
        }
    }

}
