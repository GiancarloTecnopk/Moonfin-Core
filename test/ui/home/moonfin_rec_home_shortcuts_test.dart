import 'package:flutter_test/flutter_test.dart';
import 'package:moonfin/data/models/aggregated_library.dart';
import 'package:moonfin/util/moonfin_rec_home_shortcuts.dart';

void main() {
  test('classic Android TV My Media order is deterministic', () {
    const libraries = <AggregatedLibrary>[
      AggregatedLibrary(
        id: 'series',
        name: 'Serie TV',
        collectionType: 'tvshows',
        serverId: 'srv',
      ),
      AggregatedLibrary(
        id: 'film4k',
        name: 'Film4K',
        collectionType: 'movies',
        serverId: 'srv',
      ),
      AggregatedLibrary(
        id: 'film',
        name: 'Film',
        collectionType: 'movies',
        serverId: 'srv',
      ),
      AggregatedLibrary(
        id: 'server-live',
        name: 'Live TV',
        collectionType: 'livetv',
        serverId: 'srv',
      ),
      AggregatedLibrary(
        id: 'old-recordings',
        name: 'Recordings',
        collectionType: 'recordings',
        serverId: 'srv',
      ),
    ];

    final items = buildMoonfinRecMyMediaItems(
      libraries: libraries,
      fallbackServerId: 'srv',
      liveTvLabel: 'Diretta TV',
      recordingsLabel: 'Recordings',
      includeLiveTv: true,
    );

    expect(
      items.map((item) => item.name).toList(),
      ['Diretta TV', 'Film4K', 'Film', 'Recordings', 'Serie TV'],
    );
    expect(
      items.first.rawData[moonfinRecDestinationKey],
      moonfinRecLiveTvDestination,
    );
    expect(
      items[3].rawData[moonfinRecDestinationKey],
      moonfinRecRecordingsDestination,
    );
  });

  test('does not add TV-only shortcuts when Live TV is unavailable', () {
    const libraries = <AggregatedLibrary>[
      AggregatedLibrary(
        id: 'film',
        name: 'Film',
        collectionType: 'movies',
        serverId: '',
      ),
    ];

    final items = buildMoonfinRecMyMediaItems(
      libraries: libraries,
      fallbackServerId: 'fallback',
      liveTvLabel: 'Diretta TV',
      recordingsLabel: 'Recordings',
      includeLiveTv: false,
    );

    expect(items.map((item) => item.name).toList(), ['Film']);
    expect(items.single.serverId, 'fallback');
  });
}
