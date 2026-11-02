/// Read-only playback quality diagnostics shared by Android TV and Windows.
///
/// Do not infer that the video was re-encoded merely because Jellyfin reports
/// a transcode: an audio-only transcode can keep the source video untouched.
class PlaybackQualityDiagnostics {
  const PlaybackQualityDiagnostics._();

  /// Resolve the actual selected audio stream, not the first track listed by
  /// Jellyfin. Stream indexes are global indexes across video/audio/subtitles.
  static Map<String, dynamic>? selectedAudioStream(
    List<Map<String, dynamic>> streams,
    int? selectedIndex,
  ) {
    Map<String, dynamic>? firstAudio;
    Map<String, dynamic>? defaultAudio;
    for (final stream in streams) {
      if (stream['Type']?.toString().toLowerCase() != 'audio') continue;
      firstAudio ??= stream;
      if (stream['IsDefault'] == true) defaultAudio ??= stream;
      if (selectedIndex == null) continue;
      final index = stream['Index'];
      final parsedIndex = index is int
          ? index
          : int.tryParse(index?.toString() ?? '');
      if (parsedIndex == selectedIndex) return stream;
    }
    return defaultAudio ?? firstAudio;
  }

  /// A conservative explanation of why a stream was delivered this way.
  /// HDR + HLS/transcode means possible color/tonemapping loss, not proof that
  /// the video was transcoded. Only actual FFmpeg/session details can prove it.
  static Map<String, dynamic> analyze({
    required String playMethod,
    required List<String> serverReasons,
    required String videoRange,
    String? clientReason,
  }) {
    final transcoding = playMethod.toLowerCase() == 'transcode';
    final reasons = serverReasons.map((r) => r.toLowerCase()).toList();
    final audio = reasons.any((r) => r.contains('audio')) ||
        (clientReason?.toLowerCase().contains('audio') ?? false);
    final video = reasons.any((r) =>
        r.contains('video') || r.contains('bitrate') ||
        r.contains('resolution'));
    final subtitles = reasons.any((r) => r.contains('subtitle'));
    final hdr = RegExp(
      r'HDR|DOVI|DOLBY.?VISION|HLG',
      caseSensitive: false,
    ).hasMatch(videoRange);
    final cause = !transcoding
        ? 'none'
        : audio && (video || subtitles)
            ? 'mixed'
            : audio
                ? 'audio'
                : video
                    ? 'video'
                    : subtitles
                        ? 'subtitles'
                        : 'unknown';

    return <String, dynamic>{
      'category': cause,
      'hdrSource': hdr,
      'hdrTranscodeRisk': transcoding && hdr,
      'videoReencodeSuspected': transcoding && (video || subtitles),
      'videoReencodeConfirmed': false,
      'note': !transcoding
          ? 'Direct playback: no server transcoding reported.'
          : hdr
              ? 'HDR source is using a transcode route. Check Jellyfin FFmpeg '
                  'session details to verify whether video is being '
                  're-encoded or tone-mapped; audio reasons alone do not prove it.'
              : 'Check Jellyfin FFmpeg session details before assuming the '
                  'video is being re-encoded.',
    };
  }
}
