import 'package:flutter_test/flutter_test.dart';
import 'package:moonfin/playback/playback_quality_diagnostics.dart';

void main() {
  group('Selected audio track diagnostics', () {
    final streams = <Map<String, dynamic>>[
      {'Index': 0, 'Type': 'Video', 'Codec': 'hevc'},
      {'Index': 1, 'Type': 'Audio', 'Codec': 'aac', 'Channels': 6},
      {'Index': 2, 'Type': 'Audio', 'Codec': 'ac3', 'Channels': 6},
      {'Index': 3, 'Type': 'Subtitle', 'Codec': 'subrip'},
    ];
    test('reports selected AC3 track, not first AAC track', () {
      final audio = PlaybackQualityDiagnostics.selectedAudioStream(streams, 2);
      expect(audio?['Codec'], 'ac3');
      expect(audio?['Index'], 2);
    });
    test('falls back to first audio when selection is absent or invalid', () {
      expect(
        PlaybackQualityDiagnostics.selectedAudioStream(streams, null)?['Codec'],
        'aac',
      );
      expect(
        PlaybackQualityDiagnostics.selectedAudioStream(streams, 90)?['Codec'],
        'aac',
      );
    });
    test('accepts Jellyfin string stream indexes', () {
      expect(
        PlaybackQualityDiagnostics.selectedAudioStream(
          [{'Index': '4', 'Type': 'Audio', 'Codec': 'eac3'}],
          4,
        )?['Codec'],
        'eac3',
      );
    });
  });

  group('HDR transcode risk classification', () {
    test('audio-only reason is NOT proof of video re-encoding', () {
      final analysis = PlaybackQualityDiagnostics.analyze(
        playMethod: 'transcode',
        serverReasons: ['AudioCodecNotSupported'],
        videoRange: 'HDR10',
      );
      expect(analysis['category'], 'audio');
      expect(analysis['hdrTranscodeRisk'], true);
      expect(analysis['videoReencodeSuspected'], false);
      expect(analysis['videoReencodeConfirmed'], false);
    });
    test('video codec reason is suspected HDR video re-encode', () {
      final analysis = PlaybackQualityDiagnostics.analyze(
        playMethod: 'transcode',
        serverReasons: ['VideoCodecNotSupported'],
        videoRange: 'DOVI_WITH_HDR10',
      );
      expect(analysis['category'], 'video');
      expect(analysis['hdrTranscodeRisk'], true);
      expect(analysis['videoReencodeSuspected'], true);
    });
    test('Direct Play of HDR is not flagged', () {
      final analysis = PlaybackQualityDiagnostics.analyze(
        playMethod: 'directPlay',
        serverReasons: [],
        videoRange: 'HDR10Plus',
      );
      expect(analysis['category'], 'none');
      expect(analysis['hdrTranscodeRisk'], false);
    });
    test('SDR transcode has no HDR tone mapping warning', () {
      final analysis = PlaybackQualityDiagnostics.analyze(
        playMethod: 'transcode',
        serverReasons: ['AudioChannelsNotSupported'],
        videoRange: 'SDR',
      );
      expect(analysis['category'], 'audio');
      expect(analysis['hdrTranscodeRisk'], false);
    });
    test('subtitles alone are classified independently', () {
      final analysis = PlaybackQualityDiagnostics.analyze(
        playMethod: 'transcode',
        serverReasons: ['SubtitleCodecNotSupported'],
        videoRange: 'HLG',
      );
      expect(analysis['category'], 'subtitles');
      expect(analysis['hdrTranscodeRisk'], true);
      expect(analysis['videoReencodeSuspected'], true);
    });
  });
}
