import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:moonfin/data/viewmodels/recordings_view_model.dart';
import 'package:server_core/server_core.dart';

class _Client extends Mock implements MediaServerClient {}
class _LiveTv extends Mock implements LiveTvApi {}
class _Items extends Mock implements ItemsApi {}

void main() {
  late _Client client;
  late _LiveTv liveTv;
  late _Items items;
  late RecordingsViewModel vm;

  setUp(() async {
    client = _Client(); liveTv = _LiveTv(); items = _Items();
    when(() => client.liveTvApi).thenReturn(liveTv);
    when(() => client.itemsApi).thenReturn(items);
    when(() => liveTv.getRecordings(
      limit: any(named: 'limit'), fields: any(named: 'fields'),
      enableImages: any(named: 'enableImages'), isSeries: any(named: 'isSeries'),
      isMovie: any(named: 'isMovie'), isSports: any(named: 'isSports'),
      isKids: any(named: 'isKids'),
    )).thenAnswer((_) async => {'Items': [{'Id': 'rec-1', 'Name': 'Film'}]});
    when(() => liveTv.getTimers()).thenAnswer((_) async => {'Items': []});
    vm = RecordingsViewModel(client);
    await vm.load();
  });
  tearDown(() => vm.dispose());

  test('server deletion removes the recording from all category rows', () async {
    when(() => items.deleteItem('rec-1')).thenAnswer((_) async {});
    final recording = vm.recentRecordings.single;
    vm.setFocusedItem(recording);
    await vm.deleteRecording(recording);
    verify(() => items.deleteItem('rec-1')).called(1);
    expect([vm.recentRecordings, vm.seriesRecordings, vm.movieRecordings,
      vm.sportsRecordings, vm.kidsRecordings].every((row) => row.isEmpty), isTrue);
    expect(vm.focusedItem, isNull);
  });

  test('permission or server failure keeps the recording visible', () async {
    when(() => items.deleteItem('rec-1')).thenThrow(StateError('Forbidden'));
    await expectLater(vm.deleteRecording(vm.recentRecordings.single), throwsStateError);
    expect(vm.recentRecordings.single.id, 'rec-1');
    expect(vm.movieRecordings.single.id, 'rec-1');
  });

  test('a scheduled timer cannot be sent to the item deletion endpoint', () async {
    final timer = RecordingItem(id: 'timer-1', name: 'Scheduled', rawData: {});
    await expectLater(vm.deleteRecording(timer), throwsStateError);
    verifyNever(() => items.deleteItem(any()));
  });
}
