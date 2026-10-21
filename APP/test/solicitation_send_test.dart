import 'dart:convert';

import 'package:cobrador/auth/auth_api.dart';
import 'package:cobrador/wallet/wallet_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

const session = AuthSession(
  companyCode: 'cv',
  userId: 7,
  name: 'Teste',
  login: 'teste',
  accessToken: 'old',
  refreshToken: 'refresh',
);
const payload = <String, Object?>{
  'cliente_id': 18,
  'valor_pretendido': 100,
  'frequencia_pagamento': 'Diária',
  'numero_parcelas': 10,
  'observacao': 'Teste',
};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  setUp(() => FlutterSecureStorage.setMockInitialValues({}));
  test('envia somente o pedido informado em um POST', () async {
    var calls = 0;
    final service = WalletService(
      session,
      clientFactory: () => MockClient((request) async {
        calls++;
        expect(request.method, 'POST');
        expect(request.url.path, '/api/v1/solicitacoes/');
        expect(jsonDecode(request.body), payload);
        return http.Response('{}', 201);
      }),
    );
    await service.sendSolicitation(payload);
    expect(calls, 1);
  });
  test(
    'renova token expirado e preserva o pedido na tentativa autenticada',
    () async {
      var calls = 0;
      final service = WalletService(
        session,
        clientFactory: () => MockClient((request) async {
          calls++;
          if (calls == 1) return http.Response('', 401);
          if (calls == 2) {
            expect(request.url.path, '/api/v1/auth/refresh');
            return http.Response(
              jsonEncode({
                'access_token': 'new',
                'refresh_token': 'new-refresh',
              }),
              200,
            );
          }
          expect(request.headers['Authorization'], 'Bearer new');
          expect(jsonDecode(request.body), payload);
          return http.Response('{}', 201);
        }),
      );
      await service.sendSolicitation(payload);
      expect(calls, 3);
    },
  );
  test('API sem rota informa necessidade de atualizar servidor', () async {
    final service = WalletService(
      session,
      clientFactory: () => MockClient((_) async => http.Response('', 405)),
    );
    await expectLater(
      service.sendSolicitation(payload),
      throwsA(
        isA<WalletFailure>().having(
          (e) => e.message,
          'message',
          contains('Atualize a API'),
        ),
      ),
    );
  });
}
