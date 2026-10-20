import 'dart:convert';
import 'dart:math';

import 'package:path/path.dart' as path;
import 'package:sqflite/sqflite.dart';

import '../auth/auth_api.dart';

class OperationStore {
  OperationStore(this.session);
  final AuthSession session;
  static Future<Database>? _opening;

  Future<Database> get database => _opening ??= _open();
  static Future<Database> _open() async {
    try {
      return await openDatabase(
        path.join(await getDatabasesPath(), 'operacoes.sqlite'),
        version: 1,
        onCreate: (db, _) async {
          await db.execute('''CREATE TABLE operations (
            id TEXT PRIMARY KEY, company TEXT NOT NULL, user_id INTEGER NOT NULL,
            wallet_id TEXT NOT NULL, client_id INTEGER NOT NULL,
            contract_id INTEGER NOT NULL, kind TEXT NOT NULL,
            recorded_at TEXT NOT NULL, payload TEXT NOT NULL
          )''');
          await db.execute('''CREATE TABLE visit_order (
            company TEXT NOT NULL, user_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL, position INTEGER NOT NULL,
            PRIMARY KEY(company,user_id,client_id)
          )''');
        },
      );
    } catch (_) {
      _opening = null;
      rethrow;
    }
  }

  List<Object> get owner => [session.companyCode, session.userId];

  Future<List<Map<String, Object?>>> pending() async => (await database).query(
    'operations',
    where: 'company=? AND user_id=?',
    whereArgs: owner,
    orderBy: 'recorded_at,id',
  );

  Future<Map<int, String>> answers(String wallet) async {
    final rows = await (await database).query(
      'operations',
      columns: ['contract_id', 'kind'],
      where: 'company=? AND user_id=? AND wallet_id=?',
      whereArgs: [...owner, wallet],
    );
    return {for (final r in rows) r['contract_id'] as int: r['kind'] as String};
  }

  Future<Map<int, int>> order() async {
    final rows = await (await database).query(
      'visit_order',
      where: 'company=? AND user_id=?',
      whereArgs: owner,
    );
    return {for (final r in rows) r['client_id'] as int: r['position'] as int};
  }

  Future<void> saveOrder(List<int> ids) async {
    if (ids.toSet().length != ids.length) throw StateError('Ordem inválida.');
    await (await database).transaction((txn) async {
      await txn.delete(
        'visit_order',
        where: 'company=? AND user_id=?',
        whereArgs: owner,
      );
      for (var i = 0; i < ids.length; i++) {
        await txn.insert('visit_order', {
          'company': session.companyCode,
          'user_id': session.userId,
          'client_id': ids[i],
          'position': i,
        });
      }
    });
  }

  /// Prevent duplicate pending receipts for the same installment atomically.
  Future<void> record({
    required String wallet,
    required int client,
    required List<int> contracts,
    required String kind,
    required Map<String, Object?> location,
    List<Map<String, int>> payments = const [],
  }) async {
    if (wallet.isEmpty ||
        contracts.isEmpty ||
        !['payment', 'unpaid', 'closed'].contains(kind)) {
      throw StateError('Resposta inválida.');
    }
    if (kind == 'payment' &&
        (contracts.length != 1 ||
            payments.isEmpty ||
            payments.map((p) => p['parcel_id']).toSet().length !=
                payments.length ||
            payments.any(
              (p) =>
                  p['parcel_id'] == null ||
                  (p['amount_units'] ?? 0) <= 0 ||
                  (p['balance_units'] ?? 0) <= 0,
            ))) {
      throw StateError('Recebimento inválido.');
    }
    if (location['status'] != 'captured' && location['status'] != 'timeout') {
      throw StateError('Localização obrigatória.');
    }
    if (location['status'] == 'captured' &&
        (location['latitude'] is! num || location['longitude'] is! num)) {
      throw StateError('Coordenadas inválidas.');
    }
    final now = DateTime.now().toUtc().toIso8601String();
    await (await database).transaction((txn) async {
      for (final contract in contracts) {
        final previous = await txn.query(
          'operations',
          where: 'company=? AND user_id=? AND wallet_id=? AND contract_id=?',
          whereArgs: [...owner, wallet, contract],
        );
        if (previous.isNotEmpty) {
          if (kind != 'payment' ||
              previous.any((r) => r['kind'] != 'payment')) {
            throw StateError('Contrato já possui resposta pendente.');
          }
          final alreadyReceived = <int>{};
          for (final row in previous) {
            final payload =
                jsonDecode(row['payload'] as String) as Map<String, dynamic>;
            for (final p in payload['payments'] as List) {
              alreadyReceived.add(p['parcel_id'] as int);
            }
          }
          if (payments.any((p) => alreadyReceived.contains(p['parcel_id']))) {
            throw StateError('Parcela já possui recebimento pendente.');
          }
        }
        final random = Random.secure();
        final id = List.generate(
          16,
          (_) => random.nextInt(256).toRadixString(16).padLeft(2, '0'),
        ).join();
        final items = payments.map((p) {
          final amount = p['amount_units']!;
          final balance = p['balance_units']!;
          return {
            ...p,
            'principal_units': min(amount, balance),
            'interest_units': max(amount - balance, 0),
          };
        }).toList();
        await txn.insert('operations', {
          'id': id,
          'company': session.companyCode,
          'user_id': session.userId,
          'wallet_id': wallet,
          'client_id': client,
          'contract_id': contract,
          'kind': kind,
          'recorded_at': now,
          'payload': jsonEncode({'location': location, 'payments': items}),
        });
      }
    });
  }

  Future<void> removePending(String id) async {
    await (await database).transaction((txn) async {
      final rows = await txn.query('operations',
        where: 'company=? AND user_id=? AND id=?', whereArgs: [...owner, id]);
      if (rows.isEmpty) return;
      final row = rows.single;
      if (row['kind'] == 'closed') {
        await txn.delete('operations',
          where: 'company=? AND user_id=? AND wallet_id=? AND client_id=? AND kind=?',
          whereArgs: [...owner, row['wallet_id'], row['client_id'], 'closed']);
      } else {
        await txn.delete('operations',
          where: 'company=? AND user_id=? AND id=?', whereArgs: [...owner, id]);
      }
    });
  }
}
