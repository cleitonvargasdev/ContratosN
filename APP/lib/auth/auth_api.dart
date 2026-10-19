import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';

class AuthFailure implements Exception {
  const AuthFailure(this.message);
  final String message;
}

/// Sessão apenas em memória nesta primeira etapa. Nunca persiste a senha.
class AuthSession {
  const AuthSession({required this.companyCode, required this.userId,
    required this.name, required this.login, required this.accessToken,
    required this.refreshToken});
  final String companyCode;
  final int userId;
  final String name;
  final String login;
  final String accessToken;
  final String refreshToken;
}

class AuthApi {
  AuthApi({http.Client Function()? clientFactory,
    this.timeout = const Duration(seconds: 20)})
    : _clientFactory = clientFactory ?? http.Client.new;

  final http.Client Function() _clientFactory;
  final Duration timeout;

  Future<AuthSession> login(String companyCode, String username, String password) async {
    final company = companyCode.trim().toLowerCase();
    if (company.isEmpty || username.trim().isEmpty || password.isEmpty) {
      throw const AuthFailure('Informe empresa, usuário e senha.');
    }
    final client = _clientFactory();
    try {
      final request = http.Request('POST', ApiConfig.endpoint('auth/login'))
        ..followRedirects = false
        ..headers['Accept'] = 'application/json'
        ..bodyFields = {'company_code': company, 'username': username.trim(), 'password': password};
      final tokens = await _send(client, request);
      final access = _text(tokens, 'access_token');
      final refresh = _text(tokens, 'refresh_token');
      if (tokens['token_type'] != 'bearer') throw const FormatException();

      final me = http.Request('GET', ApiConfig.endpoint('auth/me'))
        ..followRedirects = false
        ..headers['Accept'] = 'application/json'
        ..headers['Authorization'] = 'Bearer $access';
      final profile = await _send(client, me);
      if (profile['ativo'] != true) {
        throw const AuthFailure('Usuário inativo. Procure o responsável pela empresa.');
      }
      if (profile['id'] is! int) throw const FormatException();
      return AuthSession(companyCode: company, userId: profile['id'] as int,
        name: _text(profile, 'nome'), login: _text(profile, 'login'),
        accessToken: access, refreshToken: refresh);
    } on AuthFailure {
      rethrow;
    } on TimeoutException {
      throw const AuthFailure('O servidor demorou a responder. Tente novamente.');
    } on HandshakeException {
      throw const AuthFailure('Não foi possível estabelecer uma conexão segura com o servidor.');
    } on http.ClientException {
      throw const AuthFailure('Não foi possível conectar. Verifique sua internet e tente novamente.');
    } on SocketException {
      throw const AuthFailure('Não foi possível conectar. Verifique sua internet e tente novamente.');
    } on FormatException {
      throw const AuthFailure('O servidor retornou uma resposta inválida. Tente novamente mais tarde.');
    } finally {
      client.close();
    }
  }

  Future<Map<String, dynamic>> _send(http.Client client, http.Request request) async {
    final response = await (() async {
      final stream = await client.send(request);
      return http.Response.fromStream(stream);
    })().timeout(timeout);
    if (response.statusCode != 200) {
      // Não exibir respostas arbitrárias do proxy nem dados de validação
      // que possam conter as credenciais submetidas.
      throw AuthFailure(switch (response.statusCode) {
        401 => 'Usuário ou senha inválidos, ou sessão recusada. Confira os dados.',
        403 => 'Acesso negado. Confira se o funcionário está ativo e possui permissão de acesso.',
        404 => 'Empresa ou serviço não encontrado. Confira o código da empresa.',
        422 => 'Confira os dados informados para entrar.',
        429 => 'Muitas tentativas. Aguarde um pouco antes de tentar novamente.',
        _ => 'Serviço indisponível no momento. Tente novamente mais tarde.',
      });
    }
    final data = jsonDecode(utf8.decode(response.bodyBytes));
    if (data is! Map<String, dynamic>) throw const FormatException();
    return data;
  }

  String _text(Map<String, dynamic> data, String key) {
    final value = data[key];
    if (value is! String || value.isEmpty) throw const FormatException();
    return value;
  }
}
