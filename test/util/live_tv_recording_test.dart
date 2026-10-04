import 'package:flutter_test/flutter_test.dart';
import 'package:moonfin/util/live_tv_recording.dart';

void main() {
  final now = DateTime.utc(2026, 10, 4, 12);
  Map<String, dynamic> timer(String channel, String status) => {
    'Id': 'timer', 'ChannelId': channel, 'Status': status,
    'StartDate': now.subtract(const Duration(minutes: 5)).toIso8601String(),
    'EndDate': now.add(const Duration(minutes: 55)).toIso8601String(),
  };
  test('manual timer without programme metadata is found after reopening', () {
    expect(activeChannelTimerId([timer('a', 'InProgress')], 'a', now), 'timer');
    expect(activeChannelTimerId([timer('a', 'New')], 'a', now), 'timer');
  });
  test('other channels, stopped recordings and future timers are excluded', () {
    for (final status in ['Cancelled', 'Canceled', 'Completed', 'Error']) {
      expect(activeChannelTimerId([timer('a', status)], 'a', now), isNull);
    }
    expect(activeChannelTimerId([timer('b', 'InProgress')], 'a', now), isNull);
    final future = timer('a', 'New')
      ..['StartDate'] = now.add(const Duration(minutes: 10)).toIso8601String();
    expect(activeChannelTimerId([future], 'a', now), isNull);
    final ended = timer('a', 'New')..['EndDate'] = now.toIso8601String();
    expect(activeChannelTimerId([ended], 'a', now), isNull);
  });
}
