enum VisitStatus { pending, partial, partialUnpaid, paid, unpaid, closed }

VisitStatus visitStatus(List<String?> answers) {
  if (answers.isEmpty || answers.every((a) => a == null)) {
    return VisitStatus.pending;
  }
  if (answers.contains(null)) {
    return answers.contains('unpaid') ? VisitStatus.partialUnpaid : VisitStatus.partial;
  }
  if (answers.every((a) => a == 'closed')) return VisitStatus.closed;
  if (answers.contains('unpaid')) return VisitStatus.unpaid;
  if (answers.every((a) => a == 'payment')) return VisitStatus.paid;
  return VisitStatus.partial;
}

bool visitComplete(VisitStatus status) =>
    status == VisitStatus.paid ||
    status == VisitStatus.unpaid ||
    status == VisitStatus.closed;

/// API money scale: 10,000. Input accepts Brazilian decimal notation.
int parseMoney(String text) {
  final cleaned = text.trim().replaceAll('R\$', '').replaceAll(' ', '');
  if (!RegExp(r'^(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d{1,4})?$')
      .hasMatch(cleaned)) {
    throw const FormatException('Informe um valor como 1.050,00.');
  }
  final parts = cleaned.replaceAll('.', '').split(',');
  final units =
      int.parse(parts[0]) * 10000 +
      (parts.length == 2 ? int.parse(parts[1].padRight(4, '0')) : 0);
  if (units > 99999999999999) {
    throw const FormatException('Valor acima do limite permitido.');
  }
  return units;
}

String moneyInput(int units) {
  final whole = units ~/ 10000;
  final fraction = (units % 10000).toString().padLeft(4, '0');
  return '$whole,${fraction.endsWith('00') ? fraction.substring(0, 2) : fraction}';
}

String moneyLabel(int units) {
  final input = moneyInput(units).split(',');
  final whole = input[0].replaceAllMapped(
    RegExp(r'(\d)(?=(\d{3})+(?!\d))'),
    (m) => '${m[1]}.',
  );
  return 'R\$ $whole,${input[1]}';
}

List<int> distribute(int total, List<int> balances) {
  if (total <= 0 || balances.any((b) => b < 0)) {
    throw const FormatException('Informe um valor maior que zero.');
  }
  if (total > balances.fold<int>(0, (a, b) => a + b)) {
    throw const FormatException(
      'Total maior que o saldo. Informe os juros diretamente na parcela.',
    );
  }
  var remaining = total;
  return balances.map((balance) {
    final applied = remaining < balance ? remaining : balance;
    remaining -= applied;
    return applied;
  }).toList();
}

/// Compare calendar dates without timezone conversions of the due date.
bool dueByToday(Object? value, DateTime today) {
  if (value == null) return true; // Keep undated debts visible for review.
  final date = DateTime.tryParse('$value'.split('T').first);
  if (date == null) return true;
  return !DateTime(
    date.year,
    date.month,
    date.day,
  ).isAfter(DateTime(today.year, today.month, today.day));
}

bool overdue(Object? value, DateTime today) {
  if (value == null) return false;
  final date = DateTime.tryParse('$value'.split('T').first);
  return date != null &&
      DateTime(
        date.year,
        date.month,
        date.day,
      ).isBefore(DateTime(today.year, today.month, today.day));
}
