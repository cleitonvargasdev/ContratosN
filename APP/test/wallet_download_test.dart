import 'package:cobrador/sync/wallet_download.dart';
import 'package:flutter_test/flutter_test.dart';

class FakePort implements WalletDownloadPort {
  final events = <String>[];
  bool invalid = false;
  bool disconnected = false;
  bool pending = false;

  @override
  Future<void> downloadAndValidate(String id) async {
    events.add('validate');
    if (invalid) throw StateError('Arquivo inválido');
  }
  @override
  Future<void> installValidatedWallet(String id) async => events.add('install');
  @override
  Future<void> persistPendingConfirmation(String id) async {
    events.add('persist');
    pending = true;
  }
  @override
  Future<void> confirmReceiptAndDeleteRemoteZip(String id) async {
    events.add('delete');
    if (disconnected) throw StateError('Sem conexão');
  }
  @override
  Future<void> removePendingConfirmation(String id) async {
    events.add('complete');
    pending = false;
  }
}

void main() {
  test('exclui ZIP somente depois da validação e instalação local', () async {
    final port = FakePort();
    expect(await WalletDownload(port).execute('carga-1'), WalletDownloadResult.installed);
    expect(port.events, ['validate', 'install', 'persist', 'delete', 'complete']);
  });

  test('arquivo inválido não instala carteira nem pede exclusão', () async {
    final port = FakePort()..invalid = true;
    await expectLater(WalletDownload(port).execute('carga-1'), throwsStateError);
    expect(port.events, ['validate']);
  });

  test('falha de conexão preserva confirmação e permite repetir limpeza', () async {
    final port = FakePort()..disconnected = true;
    final flow = WalletDownload(port);
    expect(await flow.execute('carga-1'), WalletDownloadResult.installedCleanupPending);
    expect(port.pending, isTrue);
    port.disconnected = false;
    await flow.retryConfirmation('carga-1');
    expect(port.pending, isFalse);
    expect(port.events.where((event) => event == 'install').length, 1);
  });
}
