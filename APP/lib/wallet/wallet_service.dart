import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:isolate';

import 'package:archive/archive_io.dart';
import 'package:crypto/crypto.dart';
import 'package:http/http.dart' as http;
import 'package:path/path.dart' as path;
import 'package:sqflite/sqflite.dart';

import '../auth/auth_api.dart';
import '../auth/session_store.dart';
import '../config/api_config.dart';
import '../data/local_store.dart';
import '../operations/operation_store.dart';

class WalletFailure implements Exception {
  const WalletFailure(this.message);
  final String message;
}

bool validDownloadId(String id) =>
    RegExp(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$')
        .hasMatch(id);

/// Nenhum caminho do ZIP é utilizado como destino; aceita somente um SQLite.
void extractWallet(List<Object> args) {
  final input = InputFileStream(args[0] as String);
  try {
    final decoder = ZipDecoder();
    final archive = decoder.decodeStream(input);
    if (decoder.directory.fileHeaders.length != 1 || archive.length != 1) {
      throw const WalletFailure('Arquivo da carteira inválido.');
    }
    final entry = archive.first;
    if (entry.name != 'carteira.sqlite' ||
        !entry.isFile ||
        entry.isSymbolicLink ||
        entry.size != args[2] ||
        entry.size > 256 * 1024 * 1024) {
      throw const WalletFailure('Conteúdo da carteira inválido.');
    }
    final output = OutputFileStream(args[1] as String);
    try {
      entry.writeContent(output);
    } finally {
      output.closeSync();
    }
  } finally {
    input.closeSync();
  }
}

class WalletService {
  WalletService(this.session, {http.Client Function()? clientFactory})
    : _clientFactory = clientFactory ?? http.Client.new;
  final http.Client Function() _clientFactory;
  AuthSession session;
  final local = LocalStore.instance;

  Future<Directory> directory() async {
    final owner = sha256
        .convert(utf8.encode('${session.companyCode}:${session.userId}'))
        .toString();
    return Directory(path.join(await getDatabasesPath(), 'carteiras', owner))
        .create(recursive: true);
  }

  Future<http.StreamedResponse> _request(
    http.Client client,
    String method,
    String route, {
    bool refreshed = false,
  }) async {
    final request = http.Request(method, ApiConfig.endpoint(route))
      ..followRedirects = false
      ..headers['Authorization'] = 'Bearer ${session.accessToken}';
    final result = await client
        .send(request)
        .timeout(const Duration(seconds: 90));
    if (result.statusCode == 401 && !refreshed) {
      await result.stream.drain<void>();
      final refresh = http.Request('POST', ApiConfig.endpoint('auth/refresh'))
        ..followRedirects = false
        ..headers['Content-Type'] = 'application/json'
        ..body = jsonEncode({'refresh_token': session.refreshToken});
      final renewed = await http.Response.fromStream(
        await client.send(refresh).timeout(const Duration(seconds: 30)),
      ).timeout(const Duration(seconds: 30));
      if (renewed.statusCode != 200) {
        throw const WalletFailure(
          'Sessão expirada ou acesso revogado. Saia e entre novamente.',
        );
      }
      final data = jsonDecode(renewed.body) as Map<String, dynamic>;
      session = AuthSession(
        companyCode: session.companyCode,
        userId: session.userId,
        name: session.name,
        login: session.login,
        accessToken: data['access_token'] as String,
        refreshToken: data['refresh_token'] as String,
      );
      await SessionStore.save(session);
      return _request(client, method, route, refreshed: true);
    }
    if (result.statusCode < 200 || result.statusCode >= 300) {
      await result.stream.drain<void>();
      throw WalletFailure(switch (result.statusCode) {
        401 || 403 => 'Acesso recusado. Confira a situação do funcionário e entre novamente.',
        404 =>
          'Carteira não encontrada ou API ainda não atualizada no servidor.',
        _ =>
          'O servidor não conseguiu atender a solicitação (${result.statusCode}).',
      });
    }
    return result;
  }

  Future<int> retryCleanup() async {
    final client = _clientFactory();
    try {
      final pending = await local.pendingDownloads(
        session.companyCode,
        '${session.userId}',
      );
      for (final id in pending) {
        if (!validDownloadId(id)) continue;
        final response = await _request(
          client,
          'POST',
          'mobile/carteira/$id/confirmar',
        );
        await response.stream.drain<void>();
        await local.markDownloadRemoved(
          session.companyCode,
          '${session.userId}',
          id,
        );
      }
      return pending.length;
    } finally {
      client.close();
    }
  }

  /// Retorna false quando a carteira foi instalada mas a limpeza está pendente.
  Future<bool> download(void Function(String) progress) async {
    if ((await OperationStore(session).pending()).isNotEmpty) {
      throw const WalletFailure(
        'Há recebimentos ou ocorrências pendentes neste aparelho. '
        'A carteira será preservada até resolver essas pendências.',
      );
    }
    final client = _clientFactory();
    File? zip;
    File? sqlite;
    bool installed = false;
    try {
      progress('Preparando carteira no servidor…');
      final response = await http.Response.fromStream(
        await _request(client, 'POST', 'mobile/carteira'),
      ).timeout(const Duration(seconds: 90));
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final id = data['download_id'] as String;
      final size = data['size_bytes'] as int;
      final sqliteSize = data['sqlite_size_bytes'] as int;
      if (!validDownloadId(id) ||
          data['schema_version'] != 1 ||
          size <= 0 ||
          size > 64 * 1024 * 1024 ||
          sqliteSize <= 0 ||
          sqliteSize > 256 * 1024 * 1024) {
        throw const WalletFailure(
          'Formato ou tamanho da carteira não suportado.',
        );
      }
      final dir = await directory();
      zip = File(path.join(dir.path, '$id.zip'));
      sqlite = File(path.join(dir.path, '$id.sqlite'));
      progress('Baixando carteira…');
      final stream = await _request(
        client,
        'GET',
        'mobile/carteira/$id/arquivo',
      );
      final sink = zip.openWrite();
      var received = 0;
      try {
        await for (final chunk in stream.stream.timeout(
          const Duration(seconds: 45),
        )) {
          received += chunk.length;
          if (received > size) {
            throw const WalletFailure('Tamanho do download incorreto.');
          }
          sink.add(chunk);
        }
        await sink.flush();
      } finally {
        await sink.close();
      }
      if (received != size ||
          (await sha256.bind(zip.openRead()).first).toString() !=
              data['sha256']) {
        throw const WalletFailure(
          'Download incompleto ou inválido. Tente novamente.',
        );
      }
      progress('Validando e instalando carteira…');
      final args = <Object>[zip.path, sqlite.path, sqliteSize];
      await Isolate.run(() => extractWallet(args));
      if (await sqlite.length() != sqliteSize) {
        throw const WalletFailure('Arquivo SQLite incompleto.');
      }
      final db = await openDatabase(
        sqlite.path,
        readOnly: true,
        singleInstance: false,
      );
      try {
        final check = await db.rawQuery('PRAGMA integrity_check');
        final metadata = {
          for (final row in await db.query('metadata'))
            row['key']: row['value'],
        };
        if (check.single.values.single != 'ok' ||
            metadata['schema_version'] != '1' ||
            metadata['money_scale'] != '10000' ||
            metadata['company_code'] != session.companyCode ||
            metadata['user_id'] != '${session.userId}' ||
            metadata['download_id'] != id) {
          throw const WalletFailure(
            'A carteira é inválida ou pertence a outro usuário/empresa.',
          );
        }
        for (final table in ['clientes', 'contratos', 'parcelas']) {
          final count = Sqflite.firstIntValue(
            await db.rawQuery('SELECT COUNT(*) FROM $table'),
          );
          if (count != data[table]) {
            throw const WalletFailure('Conteúdo da carteira incompleto.');
          }
        }
      } finally {
        await db.close();
      }
      // Banco anterior só deixa de ser ativo após validar e fechar o novo.
      final oldId = await local.activeWallet(
        session.companyCode,
        '${session.userId}',
      );
      if ((await OperationStore(session).pending()).isNotEmpty) {
        throw const WalletFailure(
          'Surgiram movimentos pendentes. A carteira anterior foi preservada.',
        );
      }
      await local.activateWallet(session.companyCode, '${session.userId}', id);
      installed = true;
      if (oldId != null && validDownloadId(oldId) && oldId != id) {
        try {
          await File(path.join(dir.path, '$oldId.sqlite')).delete();
        } on FileSystemException {
          /* próxima carga pode continuar */
        }
      }
      progress('Confirmando recebimento e excluindo ZIP no servidor…');
      try {
        await retryCleanup();
        return true;
      } catch (_) {
        return false;
      }
    } on WalletFailure {
      rethrow;
    } on TimeoutException {
      throw const WalletFailure(
        'A conexão demorou a responder. A carteira anterior foi preservada.',
      );
    } on SocketException {
      throw const WalletFailure('Sem conexão. Verifique sua internet.');
    } on http.ClientException {
      throw const WalletFailure(
        'Falha na conexão segura com a API. Tente novamente.',
      );
    } catch (_) {
      throw const WalletFailure(
        'Não foi possível instalar a carteira. Tente novamente.',
      );
    } finally {
      client.close();
      if (zip != null && await zip.exists()) await zip.delete();
      if (!installed && sqlite != null && await sqlite.exists()) {
        await sqlite.delete();
      }
    }
  }

  Future<List<Map<String, Object?>>> query(
    String sql, [
    List<Object?> args = const [],
  ]) async {
    final id = await local.activeWallet(
      session.companyCode,
      '${session.userId}',
    );
    if (id == null || !validDownloadId(id)) return [];
    final file = File(path.join((await directory()).path, '$id.sqlite'));
    if (!await file.exists()) {
      throw const WalletFailure(
        'Carteira local não encontrada. Baixe novamente.',
      );
    }
    final db = await openDatabase(
      file.path,
      readOnly: true,
      singleInstance: false,
    );
    try {
      return await db.rawQuery(sql, args);
    } finally {
      await db.close();
    }
  }
}
