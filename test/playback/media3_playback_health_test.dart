import 'package:flutter_test/flutter_test.dart';
import 'package:moonfin/playback/media3_playback_health.dart';

void main() {
  test('initial load/preroll is not counted as a rebuffer', () {
    final health = Media3PlaybackHealth();
    health.state(positionMs: 0, bufferedPositionMs: 0,
        isPlaying: false, isBuffering: true);
    health.firstFrameRendered();
    health.state(positionMs: 2000, bufferedPositionMs: 15000,
        isPlaying: true, isBuffering: false);
    expect(health.rebufferCount, 0);
    expect(health.bufferedAheadMs, 13000);
  });

  test('mid-film stall after playback is counted only once', () {
    final health = Media3PlaybackHealth();
    health.state(positionMs: 4000, bufferedPositionMs: 15000,
        isPlaying: true, isBuffering: false);
    health.firstFrameRendered();
    health.state(positionMs: 14500, bufferedPositionMs: 14500,
        isPlaying: false, isBuffering: true);
    health.state(positionMs: 14500, bufferedPositionMs: 15000,
        isPlaying: false, isBuffering: true);
    expect(health.rebufferCount, 1);
    expect(
      health.technicalRows.firstWhere(
        (row) => row['label'] == 'Buffer all’ultimo blocco',
      )['value'],
      '0.0 s',
    );
  });

  test('renderer frame drops are distinct from network rebuffering', () {
    final health = Media3PlaybackHealth();
    health.firstFrameRendered();
    health.state(positionMs: 7000, bufferedPositionMs: 47000,
        isPlaying: true, isBuffering: false);
    health.droppedFrames(12);
    health.droppedFrames(3);
    health.droppedFrames(-1);
    health.videoDecoder('OMX.MTK.VIDEO.DECODER.HEVC');
    health.frameRate(content: 23.976, output: 60.0);
    expect(health.rebufferCount, 0);
    expect(health.droppedFrames, 15);
    expect(health.bufferedAheadMs, 40000);
    expect(
      health.technicalRows.firstWhere(
        (row) => row['label'] == 'Decoder video Media3',
      )['value'],
      'OMX.MTK.VIDEO.DECODER.HEVC',
    );
    expect(health.technicalRows.last['value'], '60.000 Hz');
  });

  test('new playback resets every counter and old decoder', () {
    final health = Media3PlaybackHealth();
    health.firstFrameRendered();
    health.state(positionMs: 1000, bufferedPositionMs: 5000,
        isPlaying: true, isBuffering: false);
    health.droppedFrames(8);
    health.audioUnderrun();
    health.videoDecoder('old-codec');
    health.reset();
    expect(health.droppedFrames, 0);
    expect(health.audioUnderruns, 0);
    expect(health.bufferedAheadMs, 0);
    expect(health.technicalRows.any(
      (row) => row['label'] == 'Decoder video Media3',
    ), false);
  });
}
