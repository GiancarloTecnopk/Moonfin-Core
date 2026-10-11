import '../data/models/aggregated_item.dart';
import '../data/models/aggregated_library.dart';

const moonfinRecDestinationKey = 'MoonfinRecDestination';
const moonfinRecLiveTvDestination = 'liveTv';
const moonfinRecRecordingsDestination = 'recordings';
const moonfinRecMyMediaRowId = 'moonfinRecMyMedia';

List<AggregatedItem> buildMoonfinRecMyMediaItems({
  required List<AggregatedLibrary> libraries,
  required String fallbackServerId,
  required String liveTvLabel,
  required String recordingsLabel,
  required bool includeLiveTv,
}) {
  AggregatedItem fromLibrary(AggregatedLibrary lib) => AggregatedItem(
        id: lib.id,
        serverId: lib.serverId.isNotEmpty ? lib.serverId : fallbackServerId,
        rawData: <String, dynamic>{
          'Id': lib.id,
          'Name': lib.name,
          'CollectionType': lib.collectionType,
          'Type': 'CollectionFolder',
          if (lib.primaryImageAspectRatio != null)
            'PrimaryImageAspectRatio': lib.primaryImageAspectRatio,
          if (lib.imageTags != null) 'ImageTags': lib.imageTags,
          if (lib.backdropImageTags != null)
            'BackdropImageTags': lib.backdropImageTags,
        },
      );

  bool isRecordingLibrary(AggregatedLibrary lib) {
    final type = lib.collectionType.trim().toLowerCase();
    final name = lib.name.trim().toLowerCase();
    return type == 'recordings' ||
        name == 'recordings' ||
        name == 'registrazioni';
  }

  final usable = libraries
      .where((lib) => lib.id.isNotEmpty && lib.name.trim().isNotEmpty)
      .where((lib) => lib.collectionType.trim().toLowerCase() != 'livetv')
      .where((lib) => !isRecordingLibrary(lib))
      .toList(growable: false);

  final movies = usable
      .where((lib) => lib.collectionType.trim().toLowerCase() == 'movies')
      .map(fromLibrary)
      .toList(growable: false);
  final series = usable
      .where((lib) => lib.collectionType.trim().toLowerCase() == 'tvshows')
      .map(fromLibrary)
      .toList(growable: false);
  final others = usable
      .where((lib) {
        final type = lib.collectionType.trim().toLowerCase();
        return type != 'movies' && type != 'tvshows';
      })
      .map(fromLibrary)
      .toList(growable: false);

  final items = <AggregatedItem>[];

  if (includeLiveTv) {
    items.add(
      AggregatedItem(
        id: 'moonfin-rec-live-tv',
        serverId: fallbackServerId,
        rawData: <String, dynamic>{
          'Id': 'moonfin-rec-live-tv',
          'Name': liveTvLabel,
          'CollectionType': 'livetv',
          'Type': 'CollectionFolder',
          moonfinRecDestinationKey: moonfinRecLiveTvDestination,
        },
      ),
    );
  }

  items.addAll(movies);

  if (includeLiveTv) {
    items.add(
      AggregatedItem(
        id: 'moonfin-rec-recordings',
        serverId: fallbackServerId,
        rawData: <String, dynamic>{
          'Id': 'moonfin-rec-recordings',
          'Name': recordingsLabel,
          'CollectionType': 'recordings',
          'Type': 'CollectionFolder',
          moonfinRecDestinationKey: moonfinRecRecordingsDestination,
        },
      ),
    );
  }

  items
    ..addAll(series)
    ..addAll(others);

  return items;
}
