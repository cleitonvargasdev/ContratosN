import 'dart:convert';
import 'dart:io';
import 'package:archive/archive.dart';
import 'package:cobrador/auth/auth_api.dart';
import 'package:cobrador/data/local_store.dart';
import 'package:cobrador/wallet/wallet_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

const session = AuthSession(companyCode: 'cv', userId: 7, name: 'Cobrador',
  login: 'cobrador', accessToken: 'access', refreshToken: 'refresh');

void main() {
  late Directory temp;
  late Map<String, dynamic> manifest;
  late List<int> zip;
  setUpAll(() async {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
    temp = await Directory.systemTemp.createTemp('wallet-test-');
    await databaseFactory.setDatabasesPath(temp.path);
    manifest = jsonDecode(await File('test/fixtures/manifest.json').readAsString()) as Map<String, dynamic>;
    zip = await File('test/fixtures/wallet.zip').readAsBytes();
  });

  test('instala SQLite real gerado pela API e confirma depois de persistir', () async {
    var acknowledgements = 0;
    final service = WalletService(session, clientFactory: () => MockClient((request) async {
      expect(request.headers['Authorization'], 'Bearer access');
      if (request.url.path.endsWith('/arquivo')) return http.Response.bytes(zip, 200);
      if (request.url.path.endsWith('/confirmar')) {
        expect(await LocalStore.instance.activeWallet('cv', '7'), manifest['download_id']);
        acknowledgements++;
        return http.Response('', 204);
      }
      return http.Response(jsonEncode(manifest), 201);
    }));
    expect(await service.download((_) {}), true);
    final rows = await service.query('SELECT saldo_units FROM parcelas');
    expect(rows.single['saldo_units'], 2500000);
    expect(acknowledgements, 1);
    expect(await LocalStore.instance.pendingDownloads('cv', '7'), isEmpty);
  });

  test('SHA incorreto preserva carteira anterior e não confirma exclusão', () async {
    final previous = await LocalStore.instance.activeWallet('cv', '7');
    var acknowledgements = 0;
    final service = WalletService(session, clientFactory: () => MockClient((request) async {
      if (request.url.path.endsWith('/arquivo')) return http.Response.bytes(zip, 200);
      if (request.url.path.endsWith('/confirmar')) acknowledgements++;
      return http.Response(jsonEncode({...manifest, 'sha256': 'incorrect',
        'download_id': '11111111-1111-4111-8111-111111111111'}), 201);
    }));
    await expectLater(service.download((_) {}), throwsA(isA<WalletFailure>()));
    expect(await LocalStore.instance.activeWallet('cv', '7'), previous);
    expect(acknowledgements, 0);
  });

  test('recusa arquivo válido destinado a outro usuário', () async {
    const other = AuthSession(companyCode: 'cv', userId: 8, name: 'Outro',
      login: 'outro', accessToken: 'access', refreshToken: 'refresh');
    final service = WalletService(other, clientFactory: () => MockClient((request) async {
      if (request.url.path.endsWith('/arquivo')) return http.Response.bytes(zip, 200);
      if (request.url.path.endsWith('/confirmar')) fail('Não deve confirmar carteira de outro usuário');
      return http.Response(jsonEncode(manifest), 201);
    }));
    await expectLater(service.download((_) {}), throwsA(isA<WalletFailure>()));
    expect(await LocalStore.instance.activeWallet('cv', '8'), isNull);
  });

  test('rejeita caminho de extração fora da carteira', () async {
    final archive = Archive()..add(ArchiveFile('../../escape.sqlite', 1, [0]));
    final source = File('${temp.path}/malicious.zip');
    await source.writeAsBytes(ZipEncoder().encode(archive));
    expect(() => extractWallet([source.path, '${temp.path}/target.sqlite', 1]),
      throwsA(isA<WalletFailure>()));
    expect(await File('${temp.path}/target.sqlite').exists(), false);
  });

  test('falha na exclusão mantém carteira e pendência; nova tentativa confirma', () async {
    var failCleanup = true;
    final service = WalletService(session, clientFactory: () => MockClient((request) async {
      if (request.url.path.endsWith('/arquivo')) return http.Response.bytes(zip, 200);
      if (request.url.path.endsWith('/confirmar')) return http.Response('', failCleanup ? 503 : 204);
      return http.Response(jsonEncode(manifest), 201);
    }));
    expect(await service.download((_) {}), false);
    expect(await LocalStore.instance.pendingDownloads('cv', '7'), [manifest['download_id']]);
    expect((await service.query('SELECT id FROM parcelas')).length, 1);
    failCleanup = false;
    expect(await service.retryCleanup(), 1);
    expect(await LocalStore.instance.pendingDownloads('cv', '7'), isEmpty);
  });
}
