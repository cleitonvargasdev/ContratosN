import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'auth_api.dart';

class SessionStore {
  static const _storage = FlutterSecureStorage();
  static Future<void> save(AuthSession session) => _storage.write(key: 'session_v1', value: jsonEncode({
    'company': session.companyCode, 'id': session.userId, 'name': session.name,
    'login': session.login, 'access': session.accessToken, 'refresh': session.refreshToken,
  }));
  static Future<AuthSession?> load() async {
    final raw = await _storage.read(key: 'session_v1');
    if (raw == null) return null;
    try {
      final json = jsonDecode(raw) as Map<String, dynamic>;
      return AuthSession(companyCode: json['company'] as String, userId: json['id'] as int,
        name: json['name'] as String, login: json['login'] as String,
        accessToken: json['access'] as String, refreshToken: json['refresh'] as String);
    } catch (_) {
      await clear();
      return null;
    }
  }
  static Future<void> clear() => _storage.delete(key: 'session_v1');
}
