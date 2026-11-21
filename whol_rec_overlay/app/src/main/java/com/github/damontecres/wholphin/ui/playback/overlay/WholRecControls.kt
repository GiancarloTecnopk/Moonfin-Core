package com.github.damontecres.wholphin.ui.playback.overlay

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.hilt.lifecycle.viewmodel.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.tv.material3.Button
import androidx.tv.material3.Text
import com.github.damontecres.wholphin.services.LiveTvService
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.util.UUID
import javax.inject.Inject

data class WholRecState(
    val channelId: UUID? = null,
    val recording: Boolean = false,
    val busy: Boolean = false,
    val message: String? = null,
)

@HiltViewModel
class WholRecViewModel @Inject constructor(
    private val service: LiveTvService,
) : ViewModel() {
    private val _state = MutableStateFlow(WholRecState())
    val state: StateFlow<WholRecState> = _state

    fun refresh(channelId: UUID) {
        if (_state.value.busy) return
        viewModelScope.launch {
            try {
                val active = withContext(Dispatchers.IO) {
                    service.activeManualRecording(channelId) != null
                }
                _state.value = _state.value.copy(
                    channelId = channelId,
                    recording = active,
                    // Don't erase a useful HTTP/DVR error at the next 15s poll.
                    message = if (_state.value.channelId == channelId) _state.value.message else null,
                )
            } catch (e: Exception) {
                _state.value = _state.value.copy(channelId = channelId, message = e.message)
            }
        }
    }

    fun start(channelId: UUID, channelName: String, minutes: Int) {
        if (_state.value.busy) return
        _state.value = _state.value.copy(busy = true, message = null)
        viewModelScope.launch {
            try {
                withContext(Dispatchers.IO) {
                    service.startManualRecording(channelId, channelName, minutes)
                }
                _state.value = WholRecState(
                    channelId = channelId,
                    recording = true,
                    message = "REC started on Jellyfin",
                )
            } catch (e: Exception) {
                _state.value = WholRecState(channelId = channelId, message = e.message ?: "REC failed")
            }
        }
    }

    fun stop(channelId: UUID) {
        if (_state.value.busy) return
        _state.value = _state.value.copy(busy = true, message = null)
        viewModelScope.launch {
            try {
                val stopped = withContext(Dispatchers.IO) {
                    service.stopManualRecording(channelId)
                }
                _state.value = WholRecState(
                    channelId = channelId,
                    recording = !stopped,
                    message = if (stopped) "Recording stopped" else "No manual REC timer found",
                )
            } catch (e: Exception) {
                _state.value = _state.value.copy(busy = false, message = e.message ?: "STOP REC failed")
            }
        }
    }
}

/**
 * Live TV overlay: a remote-focusable REC / STOP REC button, visible with the
 * player OSD, and an always-visible red recording indicator.
 */
@Composable
fun WholRecControls(
    channelId: UUID,
    channelName: String,
    controlsVisible: Boolean,
    modifier: Modifier = Modifier,
    viewModel: WholRecViewModel = hiltViewModel(),
) {
    val state by viewModel.state.collectAsState()
    var chooseDuration by remember(channelId) { mutableStateOf(false) }
    var confirmStop by remember(channelId) { mutableStateOf(false) }

    LaunchedEffect(channelId) {
        while (true) {
            viewModel.refresh(channelId)
            delay(15000)
        }
    }

    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.End,
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        if (state.recording && state.channelId == channelId) {
            Text("● REC", color = Color.Red, fontWeight = FontWeight.Bold)
        }
        if (controlsVisible) {
            Button(
                onClick = {
                    if (state.recording && state.channelId == channelId) confirmStop = true
                    else chooseDuration = true
                },
                enabled = !state.busy,
            ) {
                Text(if (state.recording && state.channelId == channelId) "STOP REC" else "● REC")
            }
            if (!state.message.isNullOrBlank()) {
                Text(state.message ?: "", color = Color.Yellow)
            }
        }
    }

    if (chooseDuration) {
        Dialog(onDismissRequest = { chooseDuration = false }) {
            Column(
                modifier = Modifier
                    .background(Color(0xEF202020), RoundedCornerShape(12.dp))
                    .padding(24.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text("Whol REC - " + channelName)
                Text("Record this channel on Jellyfin without EPG:")
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    for (minutes in listOf(30, 60, 120, 180)) {
                        Button(onClick = {
                            chooseDuration = false
                            viewModel.start(channelId, channelName, minutes)
                        }) {
                            Text(minutes.toString() + " min")
                        }
                    }
                }
                Button(onClick = { chooseDuration = false }) { Text("Cancel") }
            }
        }
    }

    if (confirmStop) {
        Dialog(onDismissRequest = { confirmStop = false }) {
            Column(
                modifier = Modifier
                    .background(Color(0xEF202020), RoundedCornerShape(12.dp))
                    .padding(24.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text("Stop the current recording of " + channelName + "?")
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Button(onClick = {
                        confirmStop = false
                        viewModel.stop(channelId)
                    }) { Text("STOP REC") }
                    Button(onClick = { confirmStop = false }) { Text("Keep recording") }
                }
            }
        }
    }
}
