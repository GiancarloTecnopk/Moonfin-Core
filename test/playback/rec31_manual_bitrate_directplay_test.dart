import 'package:flutter_test/flutter_test.dart';
import 'package:playback_core/playback_core.dart';

void main() {
  group('manual bitrate override vs source bitrate', () {
    test('Auto never forces a transcode', () {
      expect(bitrateChangeRequiresTranscode(null, null), isFalse);
      expect(bitrateChangeRequiresTranscode(null, 350000000), isFalse);
    });

    test('200 Mbps permits direct play for lower bitrate HEVC', () {
      expect(bitrateChangeRequiresTranscode(200, 8800000), isFalse);
      expect(bitrateChangeRequiresTranscode(200, 200000000), isFalse);
    });

    test('manual cap below source bitrate requires transcode', () {
      expect(bitrateChangeRequiresTranscode(40, 80000000), isTrue);
      expect(bitrateChangeRequiresTranscode(120, 200000000), isTrue);
    });

    test('unknown or invalid bitrate respects explicit manual cap', () {
      expect(bitrateChangeRequiresTranscode(200, null), isTrue);
      expect(bitrateChangeRequiresTranscode(200, 0), isTrue);
      expect(bitrateChangeRequiresTranscode(0, 8000000), isTrue);
    });
  });
}
