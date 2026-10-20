import 'package:cobrador/main.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('carteira vazia não oferece sincronização fictícia', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(home: HomePage(initialize: () async {})),
    );
    await tester.pumpAndSettle();
    expect(find.text('Cobranças'), findsOneWidget);
    expect(find.text('Clientes'), findsOneWidget);
    await tester.tap(find.text('Transmissão'));
    await tester.pumpAndSettle();
    expect(find.text('Entre para acessar sua carteira.'), findsOneWidget);
  });

  testWidgets('falha no armazenamento impede abrir o menu operacional', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        home: HomePage(
          initialize: () async {
            throw StateError('Banco indisponível');
          },
        ),
      ),
    );
    await tester.pumpAndSettle();
    expect(
      find.textContaining('Não foi possível abrir o banco local.'),
      findsOneWidget,
    );
    expect(find.text('Recebimentos'), findsNothing);
  });
}
