import 'package:flutter_test/flutter_test.dart';
import 'package:jellyfin_preference/jellyfin_preference.dart';
import 'package:moonfin/playback/media3_player_backend.dart';
import 'package:moonfin/preference/user_preferences.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late UserPreferences prefs;
  setUp(() async {
    SharedPreferences.setMockInitialValues({});
    final store = PreferenceStore();
    await store.init();
    prefs = UserPreferences(store);
  });

  test('Fire TV Cube 3 uses advertised P8 decoder even if MediaCodec probe misses it', () {
    expect(
      Media3PlayerBackend.doviCompatMode(
        prefs,
        deviceModel: 'AFTGAZL',
        supportsP7: false,
        supportsP8: false,
        displaySupportsDolbyVision: true,
      ),
      Media3DoviCompatMode.convert,
    );
  });

  test('Cube 3 requires a Dolby Vision capable attached display', () {
    expect(
      Media3PlayerBackend.doviCompatMode(
        prefs,
        deviceModel: 'AFTGAZL',
        supportsP7: false,
        supportsP8: false,
        displaySupportsDolbyVision: false,
      ),
      Media3DoviCompatMode.strip,
    );
  });

  test('non-Cube models do not bypass a negative P8 decoder probe', () {
    expect(
      Media3PlayerBackend.doviCompatMode(
        prefs,
        deviceModel: 'AFTOTHER',
        supportsP7: false,
        supportsP8: false,
        displaySupportsDolbyVision: true,
      ),
      Media3DoviCompatMode.strip,
    );
  });

  test('explicit P7-to-HDR10 choice wins over Cube 3 P8 fallback', () async {
    await prefs.set(UserPreferences.media3MapDolbyVisionProfile7ToHevc, true);
    expect(
      Media3PlayerBackend.doviCompatMode(
        prefs,
        deviceModel: 'AFTGAZL',
        supportsP7: false,
        supportsP8: false,
        displaySupportsDolbyVision: true,
      ),
      Media3DoviCompatMode.strip,
    );
  });

  test('a positive P7 decoder probe keeps native Dolby Vision', () {
    expect(
      Media3PlayerBackend.doviCompatMode(
        prefs,
        deviceModel: 'AFTGAZL',
        supportsP7: true,
        supportsP8: false,
        displaySupportsDolbyVision: true,
      ),
      Media3DoviCompatMode.native,
    );
  });

  test('P8 decoder on any compatible device still converts P7', () {
    expect(
      Media3PlayerBackend.doviCompatMode(
        prefs,
        deviceModel: 'OTHER',
        supportsP7: false,
        supportsP8: true,
        displaySupportsDolbyVision: true,
      ),
      Media3DoviCompatMode.convert,
    );
  });
}
