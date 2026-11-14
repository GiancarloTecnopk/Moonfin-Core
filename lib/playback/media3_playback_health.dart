/// Read-only player health counters for diagnosing HEVC/Main 10 stutter.
///
/// This class never changes playback, buffer, decoder or output settings.
/// A rebuffer means ExoPlayer returned to buffering after rendering began;
/// dropped frames with ample runway point instead toward decoding/rendering.
class Media3PlaybackHealth {
  bool _firstFrameRendered = false;
  bool _previousBuffering = false;
  bool _previousPlaying = false;
  int _aheadMs = 0;
  int _rebufferCount = 0;
  int _droppedFrames = 0;
  int _audioUnderruns = 0;
  int? _aheadAtLastRebufferMs;
  String? _videoDecoder;
  double? _contentFps;
  double? _outputFps;

  int get rebufferCount => _rebufferCount;
  int get droppedFrames => _droppedFrames;
  int get bufferedAheadMs => _aheadMs;
  int get audioUnderruns => _audioUnderruns;

  void reset() {
    _firstFrameRendered = false;
    _previousBuffering = false;
    _previousPlaying = false;
    _aheadMs = 0;
    _rebufferCount = 0;
    _droppedFrames = 0;
    _audioUnderruns = 0;
    _aheadAtLastRebufferMs = null;
    _videoDecoder = null;
    _contentFps = null;
    _outputFps = null;
  }

  void firstFrameRendered() => _firstFrameRendered = true;

  void state({
    required int positionMs,
    required int bufferedPositionMs,
    required bool isPlaying,
    required bool isBuffering,
  }) {
    _aheadMs = (bufferedPositionMs - positionMs).clamp(0, 2147483647).toInt();
    // Initial preroll is NOT a rebuffer. User pauses and initial file loading
    // must also be excluded. The transition is counted only once.
    if (_firstFrameRendered &&
        isBuffering &&
        !_previousBuffering &&
        _previousPlaying) {
      _rebufferCount++;
      _aheadAtLastRebufferMs = _aheadMs;
    }
    _previousBuffering = isBuffering;
    _previousPlaying = isPlaying;
  }

  void recordDroppedFrames(int count) {
    if (count > 0) _droppedFrames += count;
  }

  void audioUnderrun() => _audioUnderruns++;

  void videoDecoder(String name) {
    if (name.trim().isNotEmpty) _videoDecoder = name.trim();
  }

  void frameRate({double? content, double? output}) {
    if (content != null && content > 0) _contentFps = content;
    if (output != null && output > 0) _outputFps = output;
  }

  List<Map<String, dynamic>> get technicalRows => [
    if (_videoDecoder case final String decoder)
      {'label': 'Decoder video Media3', 'value': decoder},
    {'label': 'Buffer video disponibile', 'value': '${(_aheadMs / 1000).toStringAsFixed(1)} s'},
    {'label': 'Ricaricamenti buffer', 'value': '$_rebufferCount'},
    if (_aheadAtLastRebufferMs case final int ahead)
      {'label': 'Buffer all’ultimo blocco', 'value': '${(ahead / 1000).toStringAsFixed(1)} s'},
    {'label': 'Fotogrammi persi', 'value': '$_droppedFrames'},
    {'label': 'Interruzioni audio', 'value': '$_audioUnderruns'},
    if (_contentFps case final double fps)
      {'label': 'Frequenza video', 'value': '${fps.toStringAsFixed(3)} fps'},
    if (_outputFps case final double hz)
      {'label': 'Frequenza schermo', 'value': '${hz.toStringAsFixed(3)} Hz'},
  ];
}
