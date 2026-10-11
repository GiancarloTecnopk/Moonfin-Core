import 'package:playback_core/playback_core.dart';

import '../data/models/aggregated_item.dart';

bool isMoonfinRecAvcHigh10Stream(Map<dynamic, dynamic> stream) {
  final type = stream['Type']?.toString().trim().toLowerCase();
  if (type != null && type.isNotEmpty && type != 'video') return false;

  final codec = stream['Codec']?.toString().trim().toLowerCase();
  if (codec != 'h264' && codec != 'avc') return false;

  final profile = stream['Profile']?.toString().trim().toLowerCase() ?? '';
  final bitDepth = _asInt(stream['BitDepth']) ?? 0;
  return profile.contains('high 10') ||
      profile.contains('high10') ||
      bitDepth > 8;
}

bool moonfinRecItemNeedsSoftwareAvcHigh10(AggregatedItem item) {
  if (item.mediaStreams.any(isMoonfinRecAvcHigh10Stream)) return true;

  for (final source in item.mediaSources) {
    final streams = source['MediaStreams'];
    if (streams is! List) continue;
    for (final stream in streams.whereType<Map>()) {
      if (isMoonfinRecAvcHigh10Stream(stream)) return true;
    }
  }
  return false;
}

bool moonfinRecResolutionNeedsSoftwareAvcHigh10(
  StreamResolutionResult resolution,
) => resolution.mediaStreams.any(isMoonfinRecAvcHigh10Stream);

int? _asInt(dynamic value) {
  if (value is int) return value;
  if (value is num) return value.toInt();
  if (value is String) return int.tryParse(value);
  return null;
}
