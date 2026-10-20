import 'package:flutter_test/flutter_test.dart';
import 'package:cobrador/operations/collection_rules.dart';

void main() {
  test('1850 distribui 1050 e 800 sem arredondamento binário', () {
    expect(
      distribute(parseMoney('1.850,00'), [
        parseMoney('1.050,00'),
        parseMoney('1.050,00'),
        parseMoney('1.050,00'),
      ]),
      [10500000, 8000000, 0],
    );
    expect(parseMoney('12,3456'), 123456);
    expect(moneyLabel(10500000), 'R\$ 1.050,00');
    for (final invalid in ['-1', '1.05', '1,23456', 'abc', '']) {
      expect(() => parseMoney(invalid), throwsFormatException);
    }
    expect(() => distribute(201, [100, 100]), throwsFormatException);
  });
  test('verde exige resposta e pagamento de todos os contratos', () {
    expect(visitStatus(['payment', null]), VisitStatus.partial);
    expect(visitComplete(visitStatus(['payment', null])), false);
    expect(visitStatus(['payment', 'payment']), VisitStatus.paid);
    expect(visitStatus(['payment', 'unpaid']), VisitStatus.unpaid);
    expect(visitStatus(['unpaid', null]), VisitStatus.partialUnpaid);
    expect(visitComplete(visitStatus(['unpaid', null])), false);
    expect(visitStatus(['closed', 'closed']), VisitStatus.closed);
    expect(visitStatus([null, null]), VisitStatus.pending);
  });
  test('amanhã é fora da lista, hoje é visita mas não atraso', () {
    final today = DateTime(2026, 10, 20, 22);
    expect(dueByToday('2026-10-21T00:00:00+00:00', today), false);
    expect(dueByToday('2026-10-20T00:00:00+00:00', today), true);
    expect(overdue('2026-10-20', today), false);
    expect(overdue('2026-10-19', today), true);
    expect(dueByToday(null, today), true);
  });
}
