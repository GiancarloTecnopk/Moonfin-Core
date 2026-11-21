package com.github.damontecres.wholphin.services

import org.jellyfin.sdk.model.api.TimerInfoDto
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.time.OffsetDateTime
import java.time.ZoneOffset
import java.util.UUID

class WholRecTimerPolicyTest {
    private val channel = UUID.randomUUID()
    private val now = OffsetDateTime.now(ZoneOffset.UTC)

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
}
