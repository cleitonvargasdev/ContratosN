import 'dart:async';
import 'dart:convert';
import 'package:cobrador/auth/auth_api.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

http.Response tokens() => http.Response(jsonEncode({
  'access_token': 'test-access', 'refresh_token': 'test-refresh', 'token_type': 'bearer',
}), 200);

void main() {
  for (final company in ['cv', 'ms', 'bc']) {
    test('login $company envia formulário e consulta usuário com Bearer', () async {
      var calls = 0;
      final api = AuthApi(clientFactory: () => MockClient((request) async {
        calls++;
        expect(request.url.host, 'api.vstec.net');
        expect(request.url.scheme, 'https');
        expect(request.followRedirects, false);
        if (calls == 1) {
          expect(request.method, 'POST');
          expect(request.url.path, '/api/v1/auth/login');
          expect(request.headers['content-type'], contains('application/x-www-form-urlencoded'));
          expect(Uri.splitQueryString(request.body), {
            'company_code': company, 'username': 'cobrador', 'password': ' ç&+= senha ',
          });
          return tokens();
        }
        expect(request.method, 'GET');
        expect(request.url.path, '/api/v1/auth/me');
        expect(request.headers['Authorization'], 'Bearer test-access');
        return http.Response(jsonEncode({'id': 7, 'nome': 'Cobrador', 'login': 'cobrador', 'ativo': true}), 200);
      }));
      final session = await api.login(' ${company.toUpperCase()} ', ' cobrador ', ' ç&+= senha ');
      expect(session.companyCode, company);
      expect(session.userId, 7);
      expect(calls, 2);
    });
  }

  for (final status in [401, 403, 404, 422, 429, 502, 302]) {
    test('HTTP $status não cria sessão nem expõe corpo da resposta', () async {
      var calls = 0;
      final api = AuthApi(clientFactory: () => MockClient((_) async {
        calls++;
        return http.Response('segredo que não deve aparecer', status);
      }));
      await expectLater(api.login('cv', 'cobrador', 'senha'),
        throwsA(isA<AuthFailure>().having((e) => e.message, 'mensagem', isNot(contains('segredo')))));
      expect(calls, 1);
    });
  }

  test('recusa sessão quando auth/me informa funcionário inativo', () async {
    final api = AuthApi(clientFactory: () => MockClient((request) async =>
      request.method == 'POST' ? tokens() : http.Response('{"ativo":false}', 200)));
    await expectLater(api.login('cv', 'cobrador', 'senha'),
      throwsA(isA<AuthFailure>().having((e) => e.message, 'mensagem', contains('inativo'))));
  });

  test('falha na consulta do usuário impede concluir login', () async {
    final api = AuthApi(clientFactory: () => MockClient((request) async =>
      request.method == 'POST' ? tokens() : http.Response('{}', 403)));
    await expectLater(api.login('cv', 'cobrador', 'senha'), throwsA(isA<AuthFailure>()));
  });

  test('resposta inesperada é tratada sem exibir detalhes internos', () async {
    final api = AuthApi(clientFactory: () => MockClient((_) async => http.Response('<html>erro</html>', 200)));
    await expectLater(api.login('cv', 'cobrador', 'senha'), throwsA(isA<AuthFailure>()));
  });

  test('timeout encerra tentativa com mensagem recuperável', () async {
    final pending = Completer<http.Response>();
    final api = AuthApi(timeout: const Duration(milliseconds: 5),
      clientFactory: () => MockClient((_) => pending.future));
    await expectLater(api.login('cv', 'cobrador', 'senha'),
      throwsA(isA<AuthFailure>().having((e) => e.message, 'mensagem', contains('demorou'))));
    pending.complete(http.Response('{}', 500));
  });
}
