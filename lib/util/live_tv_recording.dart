/// Finds an ongoing channel recording independently of programme metadata.
String? activeChannelTimerId(
  Iterable<dynamic> timers,
  String channelId,
  DateTime now,
) {
  for (final item in timers) {
    if (item is! Map || item['ChannelId']?.toString() != channelId) continue;
    final status = item['Status']?.toString().toLowerCase();
    if (status == 'cancelled' ||
        status == 'canceled' ||
        status == 'completed' ||
        status == 'error') {
      continue;
    }
    final id = item['Id']?.toString();
    if (id == null || id.isEmpty) continue;
    final start = DateTime.tryParse(item['StartDate']?.toString() ?? '');
    final end = DateTime.tryParse(item['EndDate']?.toString() ?? '');
    if (status == 'inprogress' ||
        (start != null &&
            end != null &&
            !now.isBefore(start) &&
            now.isBefore(end))) {
      return id;
    }
  }
  return null;
}


/// One-press REC matches the stable 2.6 Android TV behavior. Existing timers
/// still go through the stop/cancel flow and scheduled series retain their menu.
bool shouldInstantRecordCurrentProgram({
  required bool isTv,
  required bool hasLiveProgram,
  required bool canRecordProgram,
  required bool hasProgramTimer,
  required bool hasSeriesTimer,
}) =>
    isTv &&
    hasLiveProgram &&
    canRecordProgram &&
    !hasProgramTimer &&
    !hasSeriesTimer;
