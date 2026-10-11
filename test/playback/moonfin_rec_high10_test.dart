import 'package:flutter_test/flutter_test.dart';
import 'package:moonfin/data/models/aggregated_item.dart';
import 'package:moonfin/playback/moonfin_rec_high10.dart';

void main() {
  group('Moonfin REC AVC High10 detection', () {
    test('detects High 10 profile', () {
      expect(
        isMoonfinRecAvcHigh10Stream({
          'Type': 'Video',
          'Codec': 'h264',
          'Profile': 'High 10',
          'BitDepth': 10,
        }),
        isTrue,
      );
    });

    test('detects 10-bit AVC even when profile text is missing', () {
      expect(
        isMoonfinRecAvcHigh10Stream({
          'Type': 'Video',
          'Codec': 'avc',
          'BitDepth': 10,
        }),
        isTrue,
      );
    });

    test('does not confuse HEVC Main10 with AVC High10', () {
      expect(
        isMoonfinRecAvcHigh10Stream({
          'Type': 'Video',
          'Codec': 'hevc',
          'Profile': 'Main 10',
          'BitDepth': 10,
        }),
        isFalse,
      );
    });

    test('finds High10 inside MediaSources on lean queue items', () {
      const item = AggregatedItem(
        id: 'episode-1',
        serverId: 'server-1',
        rawData: {
          'Id': 'episode-1',
          'MediaSources': [
            {
              'MediaStreams': [
                {
                  'Type': 'Video',
                  'Codec': 'h264',
                  'Profile': 'High 10',
                  'BitDepth': 10,
                },
              ],
            },
          ],
        },
      );

      expect(moonfinRecItemNeedsSoftwareAvcHigh10(item), isTrue);
    });
  });
}
