import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../auth/auth_api.dart';
import '../wallet/wallet_service.dart';
import 'collection_rules.dart';
import 'collection_pages.dart' show dueLabel;
import 'location_service.dart';
import 'operation_store.dart';

String shortDueLabel(Object? value) {
  final parts = '${value ?? ''}'.split('T').first.split('-');
  if (parts.length != 3 || parts[0].length != 4) return 'Sem data';
  return '${parts[2]}/${parts[1]}/${parts[0].substring(2)}';
}

/// Formats digits as Brazilian currency while the collector types.
class BrazilianCurrencyInputFormatter extends TextInputFormatter {
  const BrazilianCurrencyInputFormatter();

  @override
  TextEditingValue formatEditUpdate(
    TextEditingValue oldValue,
    TextEditingValue newValue,
  ) {
    final digits = newValue.text.replaceAll(RegExp(r'\D'), '');
    if (digits.isEmpty) return const TextEditingValue();
    final value = int.tryParse(digits);
    if (value == null) return oldValue;
    final whole = (value ~/ 100).toString().replaceAllMapped(
      RegExp(r'(\d)(?=(\d{3})+(?!\d))'),
      (match) => '${match[1]}.',
    );
    final formatted = '$whole,${(value % 100).toString().padLeft(2, '0')}';
    return TextEditingValue(
      text: formatted,
      selection: TextSelection.collapsed(offset: formatted.length),
    );
  }
}

class ReceiptPage extends StatefulWidget {
  const ReceiptPage({
    super.key,
    required this.service,
    required this.clientId,
    required this.clientName,
    required this.contractId,
    required this.walletId,
    required this.installments,
    required this.blockedIds,
    this.sentIds = const {},
    this.pendingPayments = const {},
    this.answer,
  });
  final WalletService service;
  final int clientId;
  final String clientName;
  final int contractId;
  final String walletId;
  final List<Map<String, Object?>> installments;
  final String? answer;
  final Set<int> blockedIds;
  final Set<int> sentIds;
  final Map<int, int> pendingPayments;
  @override
  State<ReceiptPage> createState() => _ReceiptPageState();
}

class _ReceiptPageState extends State<ReceiptPage> {
  static const _prefixColumnsWidth = 145.0;
  static const _markColumnWidth = 60.0;
  final _total = TextEditingController();
  late final _amounts = [
    for (final row in widget.installments)
      TextEditingController(text: moneyInput(row['saldo_units'] as int)),
  ];
  final Set<int> _selected = {};
  bool _busy = false;
  bool _saved = false;
  String? _error;
  bool get _locked => _saved;
  bool _blocked(int i) =>
      (widget.blockedIds.contains(widget.installments[i]['id']) ||
          widget.sentIds.contains(widget.installments[i]['id'])) &&
      !widget.pendingPayments.containsKey(widget.installments[i]['id']);
  bool _sent(int i) => widget.sentIds.contains(widget.installments[i]['id']);
  bool get _hasPendingPayment => widget.pendingPayments.isNotEmpty;

  @override
  void initState() {
    super.initState();
    for (var i = 0; i < widget.installments.length; i++) {
      final pending = widget.pendingPayments[widget.installments[i]['id']];
      if (pending != null) {
        _selected.add(i);
        _amounts[i].text = moneyInput(pending);
      }
    }
  }

  @override
  void dispose() {
    _total.dispose();
    for (final c in _amounts) {
      c.dispose();
    }
    super.dispose();
  }

  List<Map<String, int>> _payments() => [
    for (final i in _selected.toList()..sort())
      {
        'parcel_id': widget.installments[i]['id'] as int,
        'amount_units': parseMoney(_amounts[i].text),
        'balance_units': widget.installments[i]['saldo_units'] as int,
      },
  ];

  void _distribute() {
    try {
      final amounts = distribute(parseMoney(_total.text), [
        for (var i = 0; i < widget.installments.length; i++)
          _blocked(i) ? 0 : widget.installments[i]['saldo_units'] as int,
      ]);
      setState(() {
        _error = null;
        _selected.clear();
        for (var i = 0; i < amounts.length; i++) {
          if (amounts[i] > 0) _selected.add(i);
          _amounts[i].text = moneyInput(
            amounts[i] > 0
                ? amounts[i]
                : widget.installments[i]['saldo_units'] as int,
          );
        }
      });
    } on FormatException catch (e) {
      setState(() => _error = e.message);
    }
  }

  void _toggle(int i, bool checked) {
    if (_busy || _locked || _blocked(i)) return;
    try {
      if (checked && parseMoney(_amounts[i].text) <= 0) {
        throw const FormatException(
          'Informe um valor maior que zero antes de marcar.',
        );
      }
      setState(() {
        _error = null;
        if (checked) {
          _selected.add(i);
        } else {
          _selected.remove(i);
          _amounts[i].text = moneyInput(
            widget.installments[i]['saldo_units'] as int,
          );
        }
      });
    } on FormatException catch (e) {
      setState(() => _error = e.message);
    }
  }

  Future<void> _confirm(String kind) async {
    if (_busy || _locked) return;
    List<Map<String, int>> payments;
    try {
      payments = kind == 'payment' ? _payments() : [];
      if (kind == 'payment' &&
          (payments.isEmpty && !_hasPendingPayment ||
              payments.any((p) => p['amount_units']! <= 0))) {
        throw const FormatException(
          'Marque parcelas e informe valores maiores que zero.',
        );
      }
    } on FormatException catch (e) {
      setState(() => _error = e.message);
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final removeOnly = kind == 'payment' && payments.isEmpty;
      final location = removeOnly ? null : await OperationLocation().capture();
      // The active wallet must still be the one whose balances were displayed.
      final session = widget.service.session;
      final active = await widget.service.local.activeWallet(
        session.companyCode,
        '${session.userId}',
      );
      if (active != widget.walletId) {
        throw const FormatException('A carteira mudou. Reabra o contrato.');
      }
      if (kind == 'payment') {
        await OperationStore(session).replacePendingPayment(
          wallet: widget.walletId,
          client: widget.clientId,
          contract: widget.contractId,
          location: location,
          payments: payments,
        );
      } else {
        await OperationStore(session).record(
          wallet: widget.walletId,
          client: widget.clientId,
          contracts: [widget.contractId],
          kind: kind,
          location: location!,
          payments: payments,
        );
      }
      if (mounted) {
        setState(() => _saved = true);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              removeOnly
                  ? 'Recebimento pendente removido deste aparelho.'
                  : location!['status'] == 'timeout'
                  ? 'Salvo sem coordenadas após 30 segundos. Pendente de envio.'
                  : 'Salvo no aparelho. Pendente de envio.',
            ),
          ),
        );
        Navigator.pop(context);
      }
    } on LocationFailure catch (e) {
      if (mounted) setState(() => _error = e.message);
    } on FormatException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) {
        setState(
          () => _error = 'Não foi possível salvar. Confira os registros em Recebimentos antes de tentar novamente.',
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    var total = 0;
    var interest = 0;
    var valid = true;
    try {
      for (final p in _payments()) {
        total += p['amount_units']!;
        if (p['amount_units']! > p['balance_units']!) {
          interest += p['amount_units']! - p['balance_units']!;
        }
      }
    } on FormatException {
      valid = false;
    }
    return PopScope(
      canPop: !_busy,
      child: Scaffold(
        appBar: AppBar(title: Text('Contrato ${widget.contractId}')),
        body: SafeArea(
          top: false,
          minimum: const EdgeInsets.only(bottom: 8),
          child: ListView(
            padding: const EdgeInsets.all(8),
            children: [
              Text(
                widget.clientName,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              if (_locked)
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(16),
                    child: Text(
                      'Este contrato já tem resposta pendente. Consulte ou remova '
                      'o registro em Recebimentos para corrigir.',
                    ),
                  ),
                ),
              const SizedBox(height: 6),
              _totalHeader(),
              const SizedBox(height: 8),
              _installmentHeader(),
              for (var i = 0; i < widget.installments.length; i++)
                _installment(i),
              const SizedBox(height: 12),
              Text(
                valid
                    ? 'Total selecionado: ${moneyLabel(total)}'
                    : 'Confira os valores digitados.',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              if (valid) Text('Juros adicionais: ${moneyLabel(interest)}'),
              if (_error != null)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 12),
                  child: Semantics(
                    liveRegion: true,
                    child: Text(
                      _error!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ),
                ),
              if (_busy)
                const Column(
                  children: [
                    LinearProgressIndicator(),
                    Text(
                      'Obtendo GPS e salvando\u2026 Aguarde até 30 segundos pela localização.',
                    ),
                  ],
                ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      onPressed: _busy || _locked
                          ? null
                          : () => _confirm('unpaid'),
                      icon: const Icon(Icons.thumb_down),
                      label: const Text('Não pagou'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: FilledButton.icon(
                      onPressed: _busy || _locked || !valid
                          ? null
                          : () => _confirm('payment'),
                      icon: const Icon(Icons.check),
                      label: const Text('Confirmar'),
                    ),
                  ),
                ],
              ),
              const Text(
                'A localização é solicitada ao confirmar. Com GPS ligado e '
                'autorizado, uma tentativa sem posição por 30 segundos permite salvar sem coordenadas.',
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _totalHeader() => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 4),
    child: LayoutBuilder(
      builder: (context, constraints) {
        final valueWidth =
            constraints.maxWidth - _prefixColumnsWidth - _markColumnWidth;
        return Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            const SizedBox(width: _prefixColumnsWidth),
            SizedBox(
              width: valueWidth,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'DIGITAR VALOR',
                    style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 3),
                  SizedBox(
                    height: 40,
                    child: TextField(
                      controller: _total,
                      enabled: !_busy && !_locked,
                      textAlign: TextAlign.right,
                      style: const TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w700,
                      ),
                      inputFormatters: const [BrazilianCurrencyInputFormatter()],
                      keyboardType: const TextInputType.numberWithOptions(
                        decimal: true,
                      ),
                      decoration: const InputDecoration(
                        isDense: true,
                        prefixText: 'R\$ ',
                        border: OutlineInputBorder(),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            SizedBox(
              width: _markColumnWidth,
              child: Column(
                children: [
                  const Text(
                    'DIVIDIR',
                    style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 3),
                  Tooltip(
                    message: 'Distribuir nas parcelas',
                    child: SizedBox(
                      height: 40,
                      width: 52,
                      child: FilledButton(
                        onPressed: _busy || _locked ? null : _distribute,
                        style: FilledButton.styleFrom(padding: EdgeInsets.zero),
                        child: const Icon(Icons.attach_money, size: 24),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    ),
  );

  Widget _installmentHeader() => Padding(
    padding: const EdgeInsets.fromLTRB(4, 0, 4, 3),
    child: LayoutBuilder(
      builder: (context, constraints) {
        final valueWidth =
            constraints.maxWidth - _prefixColumnsWidth - _markColumnWidth;
        return Row(
          children: [
            const SizedBox(
              width: 35,
              child: Text(
                'PARC.',
                style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(
              width: 65,
              child: Text(
                'VENCTO',
                style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(
              width: 45,
              child: Text(
                'ATRASO',
                style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
              ),
            ),
            SizedBox(
              width: valueWidth,
              child: const Text(
                'VALOR',
                textAlign: TextAlign.right,
                style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(
              width: _markColumnWidth,
              child: Text(
                'MARCAR',
                textAlign: TextAlign.center,
                style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        );
      },
    ),
  );

  Widget _installment(int i) {
    final row = widget.installments[i];
    final selected = _selected.contains(i);
    final due = DateTime.tryParse(
      '${row['vencimento'] ?? ''}'.split('T').first,
    );
    final now = DateTime.now();
    final daysLate = due == null || !overdue(row['vencimento'], now)
        ? ''
        : '${now.difference(DateTime(due.year, due.month, due.day)).inDays}';
    return Container(
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.grey.shade300)),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final valueWidth =
              constraints.maxWidth - _prefixColumnsWidth - _markColumnWidth;
          return Row(
            children: [
              SizedBox(
                width: 35,
                child: Text(
                  '${row['numero']}',
                  style: const TextStyle(
                    color: Colors.blue,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              SizedBox(
                width: 65,
                child: Text(
                  shortDueLabel(row['vencimento']),
                  style: const TextStyle(fontSize: 12),
                ),
              ),
              SizedBox(
                width: 45,
                child: Text(
                  daysLate,
                  style: TextStyle(fontSize: 12, color: Colors.red.shade800),
                ),
              ),
              SizedBox(
                width: valueWidth,
                child: TextField(
                  controller: _amounts[i],
                  enabled: !_busy && !_locked && !_blocked(i) && !selected,
                  textAlign: TextAlign.right,
                  style: TextStyle(
                    fontSize: 12,
                    color: selected ? Colors.green.shade800 : null,
                    fontWeight: FontWeight.w700,
                  ),
                  keyboardType: const TextInputType.numberWithOptions(
                    decimal: true,
                  ),
                  decoration: const InputDecoration(
                    isDense: true,
                    border: OutlineInputBorder(),
                  ),
                  onChanged: (_) => setState(() {}),
                ),
              ),
              SizedBox(
                width: _markColumnWidth,
                child: _sent(i)
                    ? const Tooltip(
                        message: 'Recebimento enviado e confirmado',
                        child: Icon(Icons.mark_email_read, color: Colors.green),
                      )
                    : Checkbox(
                        value: selected,
                        visualDensity: VisualDensity.compact,
                        onChanged: _busy || _locked || _blocked(i)
                            ? null
                            : (checked) => _toggle(i, checked ?? false),
                      ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class PendingOperationsPage extends StatefulWidget {
  const PendingOperationsPage({super.key, required this.session});
  final AuthSession session;
  @override
  State<PendingOperationsPage> createState() => _PendingOperationsPageState();
}

class _PendingOperationsPageState extends State<PendingOperationsPage> {
  late final store = OperationStore(widget.session);
  late Future<List<Map<String, Object?>>> _rows = store.pending();
  bool _busy = false;

  Future<void> _remove(Map<String, Object?> row) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Remover resposta pendente?'),
        content: const Text(
          'Este registro ainda não foi enviado. Remova somente '
          'para corrigir uma marcação. Se recebeu dinheiro, registre o valor correto novamente. '
          'Ao remover Fechado, a ocorrência será removida de todos os contratos do cliente.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Manter'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Remover'),
          ),
        ],
      ),
    );
    if (confirm != true || !mounted) return;
    setState(() => _busy = true);
    try {
      await store.removePending(row['id'] as String);
      if (mounted) setState(() => _rows = store.pending());
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Não foi possível remover. Tente novamente.'),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Recebimentos e ocorrências')),
    body: SafeArea(
      top: false,
      minimum: const EdgeInsets.only(bottom: 12),
      child: FutureBuilder<List<Map<String, Object?>>>(
        future: _rows,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return const Center(
              child: Text('Falha ao ler os registros locais.'),
            );
          }
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final rows = snapshot.data!;
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const Card(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Text(
                    'Registros salvos neste aparelho. O envio de lotes será '
                    'habilitado após a integração com a API.',
                  ),
                ),
              ),
              if (rows.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(24),
                  child: Text('Nenhum recebimento ou ocorrência pendente.'),
                ),
              for (final row in rows) _row(row),
            ],
          );
        },
      ),
    ),
  );

  Widget _row(Map<String, Object?> row) {
    final payload =
        jsonDecode(row['payload'] as String) as Map<String, dynamic>;
    final payments = (payload['payments'] as List).cast<Map<String, dynamic>>();
    final total = payments.fold<int>(
      0,
      (sum, p) => sum + (p['amount_units'] as int),
    );
    final location = payload['location'] as Map<String, dynamic>;
    final kind = switch (row['kind']) {
      'payment' => 'Recebimento',
      'unpaid' => 'Não pagou',
      _ => 'Fechado',
    };
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '$kind \u2022 Contrato ${row['contract_id']}',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            Text(
              'Cliente ${row['client_id']} \u2022 ${dueLabel(row['recorded_at'])}',
            ),
            if (payments.isNotEmpty) ...[
              Text('Total: ${moneyLabel(total)}'),
              for (final p in payments)
                Text(
                  'Parcela ID ${p['parcel_id']}: ${moneyLabel(p['amount_units'] as int)}'
                  ' \u2022 Juros: ${moneyLabel(p['interest_units'] as int)}',
                ),
            ],
            Text(
              location['status'] == 'timeout'
                  ? 'GPS: sem posição após 30 segundos'
                  : 'GPS registrado',
            ),
            const Text('Pendente de envio'),
            TextButton.icon(
              onPressed: _busy ? null : () => _remove(row),
              icon: const Icon(Icons.edit_outlined),
              label: const Text('Remover para corrigir'),
            ),
          ],
        ),
      ),
    );
  }
}
