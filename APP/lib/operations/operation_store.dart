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
        version: 3,
        onCreate: (db, _) async {
          await db.execute('''CREATE TABLE operations (
            id TEXT PRIMARY KEY, company TEXT NOT NULL, user_id INTEGER NOT NULL,
            wallet_id TEXT NOT NULL, client_id INTEGER NOT NULL,
            contract_id INTEGER NOT NULL, kind TEXT NOT NULL,
            recorded_at TEXT NOT NULL, payload TEXT NOT NULL,
            batch_source_id TEXT, sync_status TEXT NOT NULL DEFAULT 'pending'
          )''');
          await db.execute('''CREATE TABLE visit_order (
            company TEXT NOT NULL, user_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL, position INTEGER NOT NULL,
            PRIMARY KEY(company,user_id,client_id)
          )''');
          await db.execute('''CREATE TABLE mobile_batches (
            source_id TEXT PRIMARY KEY, company TEXT NOT NULL,
            user_id INTEGER NOT NULL, server_id INTEGER,
            status TEXT NOT NULL, created_at TEXT NOT NULL
          )''');
          await db.execute('''CREATE TABLE settled_installments (
            company TEXT NOT NULL, user_id INTEGER NOT NULL, wallet_id TEXT NOT NULL,
            contract_id INTEGER NOT NULL, installment_id INTEGER NOT NULL,
            PRIMARY KEY(company,user_id,wallet_id,installment_id)
          )''');
        },
        onUpgrade: (db, oldVersion, _) async {
          if (oldVersion < 2) {
            await db.execute('ALTER TABLE operations ADD COLUMN batch_source_id TEXT');
            await db.execute("ALTER TABLE operations ADD COLUMN sync_status TEXT NOT NULL DEFAULT 'pending'");
            await db.execute('''CREATE TABLE mobile_batches (
              source_id TEXT PRIMARY KEY, company TEXT NOT NULL,
              user_id INTEGER NOT NULL, server_id INTEGER,
              status TEXT NOT NULL, created_at TEXT NOT NULL
            )''');
          }
          if (oldVersion < 3) {
            await db.execute('''CREATE TABLE settled_installments (
              company TEXT NOT NULL, user_id INTEGER NOT NULL, wallet_id TEXT NOT NULL,
              contract_id INTEGER NOT NULL, installment_id INTEGER NOT NULL,
              PRIMARY KEY(company,user_id,wallet_id,installment_id)
            )''');
          }
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

  /// Creates (or recovers) the only batch that can be in flight for this user.
  /// Its source id is persisted before the first HTTP request.
  Future<Map<String, Object?>?> prepareBatch() async {
    final db = await database;
    return db.transaction((txn) async {
      final existing = await txn.query(
        'mobile_batches',
        where: 'company=? AND user_id=? AND status IN (?,?)',
        whereArgs: [...owner, 'created', 'accepted'],
        orderBy: 'created_at',
        limit: 1,
      );
      if (existing.isNotEmpty) return existing.single;
      final rows = await txn.query(
        'operations',
        where: "company=? AND user_id=? AND kind IN ('payment','unpaid','closed') AND sync_status='pending' AND batch_source_id IS NULL",
        whereArgs: owner,
        orderBy: 'recorded_at,id',
      );
      if (rows.isEmpty) return null;
      final sourceId = _newId();
      final now = DateTime.now().toUtc().toIso8601String();
      await txn.insert('mobile_batches', {
        'source_id': sourceId,
        'company': session.companyCode,
        'user_id': session.userId,
        'status': 'created',
        'created_at': now,
      });
      await txn.update(
        'operations',
        {'batch_source_id': sourceId},
        where: "company=? AND user_id=? AND kind IN ('payment','unpaid','closed') AND sync_status='pending' AND batch_source_id IS NULL",
        whereArgs: owner,
      );
      return {
        'source_id': sourceId,
        'server_id': null,
        'status': 'created',
        'created_at': now,
      };
    });
  }

  Future<List<Map<String, Object?>>> batchOperations(String sourceId) async =>
      (await database).query(
        'operations',
        where: 'company=? AND user_id=? AND batch_source_id=?',
        whereArgs: [...owner, sourceId],
        orderBy: 'recorded_at,id',
      );

  Future<void> acceptBatch(String sourceId, int serverId) async {
    await (await database).update(
      'mobile_batches',
      {'server_id': serverId, 'status': 'accepted'},
      where: 'source_id=? AND company=? AND user_id=?',
      whereArgs: [sourceId, ...owner],
    );
  }

  /// Removes only confirmed operations. Conflicted operations stay locally
  /// marked as blocked and cannot silently enter a later batch.
  Future<void> applyBatchResult(
    String sourceId,
    List<Map<String, Object?>> items,
  ) async {
    await (await database).transaction((txn) async {
      final operations = await txn.query(
        'operations',
        where: 'company=? AND user_id=? AND batch_source_id=?',
        whereArgs: [...owner, sourceId],
      );
      for (final operation in operations) {
        final id = operation['id'] as String;
        final relevant = (operation['kind'] == 'payment')
            ? items.where((item) => (item['source_item_id'] as String).startsWith('$id:')).toList()
            : items.where((item) => item['source_item_id'] == id).toList();
        if (relevant.isEmpty || relevant.any((item) => item['blocked'] == true)) {
          await txn.update('operations', {'sync_status': 'blocked'},
              where: 'id=?', whereArgs: [id]);
        } else if (relevant.every((item) => item['processed'] == true)) {
          await txn.delete('operations', where: 'id=?', whereArgs: [id]);
        }
        if (operation['kind'] == 'payment') {
          for (final item in relevant.where((item) => item['processed'] == true)) {
            final installmentId = item['installment_id'];
            if (installmentId is int) {
              await txn.insert('settled_installments', {
                'company': session.companyCode,
                'user_id': session.userId,
                'wallet_id': operation['wallet_id'],
                'contract_id': operation['contract_id'],
                'installment_id': installmentId,
              }, conflictAlgorithm: ConflictAlgorithm.ignore);
            }
          }
        }
      }
      await txn.update('mobile_batches', {'status': 'finished'},
          where: 'source_id=?', whereArgs: [sourceId]);
    });
  }

  static String _newId() {
    final random = Random.secure();
    return List.generate(16, (_) => random.nextInt(256).toRadixString(16).padLeft(2, '0')).join();
  }

  Future<Map<int, String>> answers(String wallet) async {
    final rows = await (await database).query(
      'operations',
      columns: ['contract_id', 'kind'],
      where: 'company=? AND user_id=? AND wallet_id=?',
      whereArgs: [...owner, wallet],
    );
    final result = {for (final r in rows) r['contract_id'] as int: r['kind'] as String};
    final settled = await (await database).query(
      'settled_installments', columns: ['contract_id'],
      where: 'company=? AND user_id=? AND wallet_id=?', whereArgs: [...owner, wallet],
    );
    for (final row in settled) {
      result[row['contract_id'] as int] = 'payment';
    }
    return result;
  }

  Future<Map<int, Set<int>>> settledInstallments(String wallet) async {
    final rows = await (await database).query(
      'settled_installments', where: 'company=? AND user_id=? AND wallet_id=?',
      whereArgs: [...owner, wallet],
    );
    final result = <int, Set<int>>{};
    for (final row in rows) {
      result.putIfAbsent(row['contract_id'] as int, () => <int>{})
          .add(row['installment_id'] as int);
    }
    return result;
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
    if (ids.toSet().length != ids.length) throw StateError('Ordem inv�lida.');
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
    Map<String, Object?> extra = const {},
  }) async {
    if (wallet.isEmpty ||
        contracts.isEmpty ||
        !['payment', 'unpaid', 'closed', 'solicitation'].contains(kind)) {
      throw StateError('Resposta inv�lida.');
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
      throw StateError('Recebimento inv�lido.');
    }
    if (kind != 'solicitation' &&
        location['status'] != 'captured' &&
        location['status'] != 'timeout') {
      throw StateError('Localiza��o obrigat�ria.');
    }
    if (kind != 'solicitation' &&
        location['status'] == 'captured' &&
        (location['latitude'] is! num || location['longitude'] is! num)) {
      throw StateError('Coordenadas inv�lidas.');
    }
    final now = DateTime.now().toUtc().toIso8601String();
    await (await database).transaction((txn) async {
      // "Fechado" is a client-level occurrence replicated to each contract.
      // A receipt for any one contract corrects that occurrence for the client.
      if (kind == 'payment') {
        await txn.delete(
          'operations',
          where: 'company=? AND user_id=? AND wallet_id=? AND client_id=? AND kind=?',
          whereArgs: [...owner, wallet, client, 'closed'],
        );
      }
      for (final contract in contracts) {
        final previous = await txn.query(
          'operations',
          where: 'company=? AND user_id=? AND wallet_id=? AND contract_id=?',
          whereArgs: [...owner, wallet, contract],
        );
        if (previous.isNotEmpty) {
          await txn.delete(
            'operations',
            where: 'company=? AND user_id=? AND wallet_id=? AND contract_id=?',
            whereArgs: [...owner, wallet, contract],
          );
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
          'payload': jsonEncode({
            'location': location,
            'payments': items,
            ...extra,
          }),
        });
      }
    });
  }

  /// Replaces every unsent receipt for one contract in a single transaction.
  /// An empty list deliberately removes its previous local receipt.
  Future<void> replacePendingPayment({
    required String wallet,
    required int client,
    required int contract,
    Map<String, Object?>? location,
    required List<Map<String, int>> payments,
  }) async {
    if (wallet.isEmpty ||
        payments.map((p) => p['parcel_id']).toSet().length != payments.length ||
        payments.any(
          (p) =>
              p['parcel_id'] == null ||
              (p['amount_units'] ?? 0) <= 0 ||
              (p['balance_units'] ?? 0) <= 0,
        )) {
      throw StateError('Recebimento inv�lido.');
    }
    if (payments.isNotEmpty && location == null) {
      throw StateError('Localiza��o obrigat�ria.');
    }
    if (location != null &&
        location['status'] != 'captured' &&
        location['status'] != 'timeout') {
      throw StateError('Localiza��o obrigat�ria.');
    }
    if (location?['status'] == 'captured' &&
        (location!['latitude'] is! num || location['longitude'] is! num)) {
      throw StateError('Coordenadas inv�lidas.');
    }
    await (await database).transaction((txn) async {
      // Saving a receipt supersedes the client-wide "Fechado" occurrence,
      // including the copies recorded for its other contracts.
      if (payments.isNotEmpty) {
        await txn.delete(
          'operations',
          where: 'company=? AND user_id=? AND wallet_id=? AND client_id=? AND kind=?',
          whereArgs: [...owner, wallet, client, 'closed'],
        );
      }
      await txn.delete(
        'operations',
        where: 'company=? AND user_id=? AND wallet_id=? AND contract_id=?',
        whereArgs: [...owner, wallet, contract],
      );
      if (payments.isEmpty) return;
      final random = Random.secure();
      final id = List.generate(
        16,
        (_) => random.nextInt(256).toRadixString(16).padLeft(2, '0'),
      ).join();
      final items = payments.map((payment) {
        final amount = payment['amount_units']!;
        final balance = payment['balance_units']!;
        return {
          ...payment,
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
        'kind': 'payment',
        'recorded_at': DateTime.now().toUtc().toIso8601String(),
        'payload': jsonEncode({'location': location, 'payments': items}),
      });
    });
  }

  Future<void> discardPending(Set<String> ids) async {
    if (ids.isEmpty) return;
    await (await database).transaction((txn) async {
      for (final id in ids) {
        await txn.delete(
          'operations',
          where: 'company=? AND user_id=? AND id=?',
          whereArgs: [...owner, id],
        );
      }
    });
  }

  Future<void> removePending(String id) async {
    await (await database).transaction((txn) async {
      final rows = await txn.query(
        'operations',
        where: 'company=? AND user_id=? AND id=?',
        whereArgs: [...owner, id],
      );
      if (rows.isEmpty) return;
      final row = rows.single;
      if (row['kind'] == 'closed') {
        await txn.delete(
          'operations',
          where: 'company=? AND user_id=? AND wallet_id=? AND client_id=? AND kind=?',
          whereArgs: [...owner, row['wallet_id'], row['client_id'], 'closed'],
        );
      } else {
        await txn.delete(
          'operations',
          where: 'company=? AND user_id=? AND id=?',
          whereArgs: [...owner, id],
        );
      }
    });
  }
}
