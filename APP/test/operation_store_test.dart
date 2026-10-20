import 'dart:convert';
import 'dart:io';

import 'package:cobrador/auth/auth_api.dart';
import 'package:cobrador/operations/operation_store.dart';
import 'package:cobrador/wallet/wallet_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/testing.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

AuthSession session(String company, int id) => AuthSession(
  companyCode: company,
  userId: id,
  name: 'Teste',
  login: 'teste',
  accessToken: 'a',
  refreshToken: 'r',
);
const location = {'status': 'timeout', 'latitude': null, 'longitude': null};

void main() {
  late OperationStore store;
  setUpAll(() async {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
    final temp = await Directory.systemTemp.createTemp('operations-test-');
    await databaseFactory.setDatabasesPath(temp.path);
    store = OperationStore(session('cv', 7));
  });

  test(
    'juros separados, outras parcelas permitidas, duplicata rejeitada',
    () async {
      await store.record(
        wallet: 'wallet',
        client: 1,
        contracts: [10],
        kind: 'payment',
        location: location,
        payments: [
          {'parcel_id': 1, 'amount_units': 11000000, 'balance_units': 10500000},
        ],
      );
      final rows = await store.pending();
      final payment =
          (jsonDecode(rows.single['payload'] as String)['payments'] as List)
              .single;
      expect(payment['principal_units'], 10500000);
      expect(payment['interest_units'], 500000);
      await expectLater(
        store.record(
          wallet: 'wallet',
          client: 1,
          contracts: [10],
          kind: 'payment',
          location: location,
          payments: [
            {'parcel_id': 1, 'amount_units': 100, 'balance_units': 100},
          ],
        ),
        throwsStateError,
      );
      await store.record(
        wallet: 'wallet',
        client: 1,
        contracts: [10],
        kind: 'payment',
        location: location,
        payments: [
          {'parcel_id': 2, 'amount_units': 8000000, 'balance_units': 10500000},
        ],
      );
      expect((await store.pending()).length, 2);
      expect(await OperationStore(session('cv', 8)).pending(), isEmpty);
      expect(await OperationStore(session('other', 7)).pending(), isEmpty);
      await OperationStore(session('cv', 8))
          .removePending(rows.single['id'] as String);
      expect((await store.pending()).length, 2);
    },
  );

  test('recebimento pendente pode ser substituído ou desmarcado', () async {
    await store.replacePendingPayment(
      wallet: 'wallet', client: 3, contract: 50, location: location,
      payments: [
        {'parcel_id': 8, 'amount_units': 8000000, 'balance_units': 10500000},
      ],
    );
    var rows = (await store.pending()).where((row) => row['contract_id'] == 50);
    expect(rows, hasLength(1));
    var payment = (jsonDecode(rows.single['payload'] as String)['payments'] as List).single;
    expect(payment['amount_units'], 8000000);
    await store.replacePendingPayment(
      wallet: 'wallet', client: 3, contract: 50, location: location, payments: const [],
    );
    rows = (await store.pending()).where((row) => row['contract_id'] == 50);
    expect(rows, isEmpty);
  });

  test(
    'fechado em grupo é atômico quando um contrato já tem resposta',
    () async {
      await expectLater(
        store.record(
          wallet: 'wallet',
          client: 1,
          contracts: [11, 10],
          kind: 'closed',
          location: location,
        ),
        throwsStateError,
      );
      expect((await store.answers('wallet')).containsKey(11), false);
    },
  );

  test(
    'carteira nova bloqueada antes da rede quando existem pendências',
    () async {
      final service = WalletService(
        session('cv', 7),
        clientFactory: () =>
            MockClient((_) async => throw StateError('Não deve acessar rede')),
      );
      await expectLater(
        service.download((_) {}),
        throwsA(isA<WalletFailure>()),
      );
      expect((await store.pending()).length, 2);
    },
  );

  test('ordem fica isolada por usuário e empresa', () async {
    await store.saveOrder([3, 1, 2]);
    expect(await store.order(), {3: 0, 1: 1, 2: 2});
    expect(await OperationStore(session('cv', 8)).order(), isEmpty);
    await store.saveOrder([2, 3, 1]);
    expect(await store.order(), {2: 0, 3: 1, 1: 2});
  });

  test('corrigir Fechado remove a ocorrência de todos os contratos do cliente', () async {
    await store.record(wallet: 'wallet', client: 2, contracts: [30, 40],
      kind: 'closed', location: location);
    final rows = await store.pending();
    final closed = rows.where((r) => r['kind'] == 'closed').toList();
    expect(closed.length, 2);
    await store.removePending(closed.first['id'] as String);
    expect((await store.pending()).where((r) => r['kind'] == 'closed'), isEmpty);
    expect((await store.pending()).length, 2);
  });
}
