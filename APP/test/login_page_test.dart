import 'dart:async';
import 'package:cobrador/auth/auth_api.dart';
import 'package:cobrador/auth/login_page.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

class FakeAuth extends AuthApi {
  int calls = 0;
  final result = Completer<AuthSession>();
  @override
  Future<AuthSession> login(String companyCode, String username, String password) {
    calls++;
    return result.future;
  }
}

void main() {
  testWidgets('valida campos, impede envio repetido e mostra erro', (tester) async {
    final api = FakeAuth();
    var loggedIn = false;
    await tester.pumpWidget(MaterialApp(home: LoginPage(api: api,
      onAuthenticated: (_) => loggedIn = true)));
    await tester.ensureVisible(find.text('Entrar'));
    await tester.tap(find.text('Entrar'));
    await tester.pump();
    expect(api.calls, 0);
    expect(find.text('Informe o código da empresa.'), findsOneWidget);
    final fields = find.byType(TextFormField);
    await tester.enterText(fields.at(0), 'cv');
    await tester.enterText(fields.at(1), 'cobrador');
    await tester.enterText(fields.at(2), 'senha');
    await tester.ensureVisible(find.text('Entrar'));
    await tester.tap(find.text('Entrar'));
    await tester.pump();
    expect(find.text('Entrando…'), findsOneWidget);
    expect(tester.widget<FilledButton>(find.byType(FilledButton)).onPressed, isNull);
    expect(api.calls, 1);
    api.result.completeError(const AuthFailure('Acesso negado.'));
    await tester.pumpAndSettle();
    expect(find.text('Acesso negado.'), findsOneWidget);
    expect(loggedIn, false);
    expect(find.text('Entrar'), findsOneWidget);
  });
}
