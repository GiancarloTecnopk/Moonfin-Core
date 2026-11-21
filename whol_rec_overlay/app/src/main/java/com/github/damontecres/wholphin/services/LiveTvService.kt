package com.github.damontecres.wholphin.services

import com.github.damontecres.wholphin.data.model.BaseItem
import com.github.damontecres.wholphin.ui.toServerString
import org.jellyfin.sdk.api.client.ApiClient
import org.jellyfin.sdk.api.client.extensions.liveTvApi
import org.jellyfin.sdk.model.api.TimerInfoDto
import java.time.OffsetDateTime
import java.time.ZoneOffset
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Wholphin REC: Jellyfin DVR controller. Recording happens on the server,
 * not through the TV player, so closing playback must not end the recording.
 */
@Singleton
class LiveTvService @Inject constructor(
    private val api: ApiClient,
) {
    suspend fun fetchProgramForDialog(programId: UUID): BaseItem =
        BaseItem(api.liveTvApi.getProgram(programId.toServerString()).content)

    suspend fun cancelRecording(series: Boolean, timerId: String?): Boolean =
        if (timerId != null) {
            if (series) api.liveTvApi.cancelSeriesTimer(timerId)
            else api.liveTvApi.cancelTimer(timerId)
            true
        } else false

    suspend fun record(programId: UUID, series: Boolean) {
        val d by api.liveTvApi.getDefaultTimer(programId.toServerString())
        if (series) {
            api.liveTvApi.createSeriesTimer(d)
        } else {
            api.liveTvApi.createTimer(
                TimerInfoDto(
                    id = d.id,
                    type = d.type,
                    serverId = d.serverId,
                    externalId = d.externalId,
                    channelId = d.channelId,
                    externalChannelId = d.externalChannelId,
                    channelName = d.channelName,
                    programId = d.programId,
                    externalProgramId = d.externalProgramId,
                    name = d.name,
                    overview = d.overview,
                    startDate = d.startDate,
                    endDate = d.endDate,
                    serviceName = d.serviceName,
                    priority = d.priority,
                    prePaddingSeconds = d.prePaddingSeconds,
                    postPaddingSeconds = d.postPaddingSeconds,
                    isPrePaddingRequired = d.isPrePaddingRequired,
                    isPostPaddingRequired = d.isPostPaddingRequired,
                    keepUntil = d.keepUntil,
                ),
            )
        }
    }

    /** Manual REC also works when this channel has no EPG entry. */
    suspend fun startManualRecording(
        channelId: UUID,
        channelName: String,
        minutes: Int = 120,
    ) {
        require(minutes in 1..480) { "Recording duration must be between 1 and 480 minutes" }
        check(activeManualRecording(channelId) == null) { "A Whol REC recording is already active" }
        val now = OffsetDateTime.now(ZoneOffset.UTC)
        val timer = TimerInfoDto(
            channelId = channelId,
            channelName = channelName,
            name = "Whol REC - " + channelName,
            startDate = now.minusSeconds(5),
            endDate = now.plusMinutes(minutes.toLong()),
            prePaddingSeconds = 0,
            postPaddingSeconds = 0,
            isPrePaddingRequired = false,
            isPostPaddingRequired = false,
        )
        api.liveTvApi.createTimer(timer)
    }

    /** Never cancel a different programme/series timer when stopping manual REC. */
    suspend fun activeManualRecording(channelId: UUID): TimerInfoDto? {
        val timers by api.liveTvApi.getTimers(channelId = channelId.toServerString())
        val now = OffsetDateTime.now(ZoneOffset.UTC)
        return selectActiveWholRecTimer(timers.items, channelId, now)
    }

    suspend fun stopManualRecording(channelId: UUID): Boolean {
        val timerId = activeManualRecording(channelId)?.id ?: return false
        api.liveTvApi.cancelTimer(timerId)
        return true
    }
}

/**
 * Isolated logic so a manual timer can be differentiated from programmes
 * scheduled by Jellyfin or another device.
 */
internal fun selectActiveWholRecTimer(
    timers: List<TimerInfoDto>,
    channelId: UUID,
    now: OffsetDateTime,
): TimerInfoDto? = timers.firstOrNull { timer ->
    timer.channelId == channelId &&
        timer.name?.startsWith("Whol REC - ") == true &&
        !timer.id.isNullOrEmpty() &&
        timer.startDate?.isAfter(now) == false &&
        timer.endDate?.isAfter(now) == true
}
