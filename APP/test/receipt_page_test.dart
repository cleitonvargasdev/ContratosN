import 'package:cobrador/auth/auth_api.dart';
import 'package:cobrador/operations/receipt_page.dart';
import 'package:cobrador/wallet/wallet_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

const session = AuthSession(companyCode: 'cv', userId: 7, name: 'Teste',
  login: 'teste', accessToken: 'a', refreshToken: 'r');

Widget screen({Set<int> blocked = const {}, Map<int, int> pending = const {}}) => MaterialApp(home: ReceiptPage(
  service: WalletService(session), clientId: 1, clientName: 'Cliente teste',
  contractId: 10, walletId: 'wallet', blockedIds: blocked,
  pendingPayments: pending,
  answer: blocked.isEmpty ? null : 'payment',
  installments: [
    for (var i = 1; i <= 2; i++)
      {'id': i, 'numero': i, 'vencimento': '2026-10-20', 'saldo_units': 10500000},
  ],
));

void main() {
  testWidgets('distribui 1850 e mostra o total antes de confirmar', (tester) async {
    tester.view.physicalSize = const Size(400, 1600);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(screen());
    await tester.enterText(find.byType(TextField).first, '1.850,00');
    await tester.tap(find.byTooltip('Distribuir nas parcelas'));
    await tester.pump();
    expect(tester.widget<TextField>(find.byType(TextField).at(1)).controller!.text, '1050,00');
    expect(tester.widget<TextField>(find.byType(TextField).at(2)).controller!.text, '800,00');
    expect(find.text('Total selecionado: R\$ 1.850,00'), findsOneWidget);
    await tester.tap(find.byType(Checkbox).first);
    await tester.pump();
    expect(tester.widget<TextField>(find.byType(TextField).at(1)).controller!.text, '1050,00');
    await tester.enterText(find.byType(TextField).at(1), '1.100,00');
    await tester.tap(find.byType(Checkbox).first);
    await tester.pump();
    expect(find.text('Juros adicionais: R\$ 50,00'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('pendência bloqueia só sua parcela e distribuição ignora ela', (tester) async {
    tester.view.physicalSize = const Size(360, 1600);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(screen(blocked: {1}));
    expect(tester.widget<Checkbox>(find.byType(Checkbox).first).onChanged, isNull);
    expect(tester.widget<Checkbox>(find.byType(Checkbox).last).onChanged, isNotNull);
    await tester.enterText(find.byType(TextField).first, '200,00');
    await tester.tap(find.byTooltip('Distribuir nas parcelas'));
    await tester.pump();
    expect(tester.widget<Checkbox>(find.byType(Checkbox).first).value, false);
    expect(tester.widget<Checkbox>(find.byType(Checkbox).last).value, true);
    expect(tester.widget<TextField>(find.byType(TextField).at(2)).controller!.text, '200,00');
    expect(tester.takeException(), isNull);
  });

  testWidgets('parcial pendente fica bloqueado até desmarcar', (tester) async {
    await tester.pumpWidget(screen(blocked: {1}, pending: {1: 8000000}));
    final field = tester.widget<TextField>(find.byType(TextField).at(1));
    expect(field.controller!.text, '800,00');
    expect(field.enabled, false);
    await tester.tap(find.byType(Checkbox).first);
    await tester.pump();
    expect(tester.widget<TextField>(find.byType(TextField).at(1)).controller!.text, '1050,00');
    expect(tester.widget<TextField>(find.byType(TextField).at(1)).enabled, true);
    expect(tester.takeException(), isNull);
  });
}
