import 'package:path/path.dart' as path;
import 'package:sqflite/sqflite.dart';

/// Movimentações persistentes, separadas da carteira substituída no download.
class LocalStore {
  LocalStore._();
  static final instance = LocalStore._();
  Database? _database;

  Future<void> initialize() async {
    if (_database != null) return;
    _database = await openDatabase(
      path.join(await getDatabasesPath(), 'movimentacoes.sqlite'),
      version: 2,
      onCreate: (db, version) async {
        // A confirmação fica persistida para repetir a limpeza após uma falha
        // de conexão. Não armazenar URLs arbitrárias nem senhas nesta tabela.
        await db.execute('''
          CREATE TABLE download_confirmations (
            tenant_code TEXT NOT NULL,
            user_id TEXT NOT NULL,
            download_id TEXT NOT NULL,
            validated_at TEXT NOT NULL,
            PRIMARY KEY (tenant_code, user_id, download_id)
          )
        ''');
        await _createWalletTable(db);
      },
      onUpgrade: (db, oldVersion, newVersion) async {
        if (oldVersion < 2) await _createWalletTable(db);
      },
    );
  }

  static Future<void> _createWalletTable(Database db) => db.execute('''
    CREATE TABLE active_wallets (
      tenant_code TEXT NOT NULL, user_id TEXT NOT NULL, download_id TEXT NOT NULL,
      PRIMARY KEY (tenant_code, user_id)
    )
  ''');

  Future<String?> activeWallet(String company, String user) async {
    await initialize();
    final rows = await _database!.query('active_wallets',
      where: 'tenant_code = ? AND user_id = ?', whereArgs: [company, user]);
    return rows.isEmpty ? null : rows.single['download_id'] as String;
  }

  Future<void> activateWallet(String company, String user, String downloadId) async {
    await initialize();
    // Ponteiro da carteira e confirmação pendente são persistidos juntos.
    await _database!.transaction((txn) async {
      await txn.insert('active_wallets', {'tenant_code': company, 'user_id': user,
        'download_id': downloadId}, conflictAlgorithm: ConflictAlgorithm.replace);
      await txn.insert('download_confirmations', {'tenant_code': company, 'user_id': user,
        'download_id': downloadId, 'validated_at': DateTime.now().toUtc().toIso8601String()},
        conflictAlgorithm: ConflictAlgorithm.ignore);
    });
  }

  Future<void> recordValidatedDownload({
    required String tenantCode,
    required String userId,
    required String downloadId,
  }) async {
    await initialize();
    await _database!.insert('download_confirmations', {
      'tenant_code': tenantCode,
      'user_id': userId,
      'download_id': downloadId,
      'validated_at': DateTime.now().toUtc().toIso8601String(),
    }, conflictAlgorithm: ConflictAlgorithm.ignore);
  }

  Future<List<String>> pendingDownloads(String tenantCode, String userId) async {
    await initialize();
    final rows = await _database!.query('download_confirmations',
      columns: ['download_id'],
      where: 'tenant_code = ? AND user_id = ?',
      whereArgs: [tenantCode, userId],
    );
    return rows.map((row) => row['download_id']! as String).toList();
  }

  Future<void> markDownloadRemoved(String tenantCode, String userId, String downloadId) async {
    await initialize();
    await _database!.delete('download_confirmations',
      where: 'tenant_code = ? AND user_id = ? AND download_id = ?',
      whereArgs: [tenantCode, userId, downloadId],
    );
  }
}
