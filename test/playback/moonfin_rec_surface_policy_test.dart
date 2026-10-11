import 'package:flutter_test/flutter_test.dart';
import 'package:moonfin/playback/moonfin_rec_surface_policy.dart';

void main() {
  test('High10 software path disables Android native surface', () {
    expect(
      moonfinRecUsesNativeVideoSurface(
        platformUsesNativeSurface: true,
        forceTextureSurface: true,
      ),
      isFalse,
    );
  });

  test('High10 software path disables hardware decode', () {
    expect(
      moonfinRecHardwareDecodeEnabled(
        preferenceEnabled: true,
        forceSoftwareDecode: true,
      ),
      isFalse,
    );
  });

  test('ordinary Android TV playback keeps native hardware path', () {
    expect(
      moonfinRecUsesNativeVideoSurface(
        platformUsesNativeSurface: true,
        forceTextureSurface: false,
      ),
      isTrue,
    );
    expect(
      moonfinRecHardwareDecodeEnabled(
        preferenceEnabled: true,
        forceSoftwareDecode: false,
      ),
      isTrue,
    );
  });
}
