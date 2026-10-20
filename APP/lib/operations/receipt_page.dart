import 'dart:convert';

import 'package:flutter/material.dart';

import '../auth/auth_api.dart';
import '../wallet/wallet_service.dart';
import 'collection_rules.dart';
import 'collection_pages.dart' show dueLabel;
import 'location_service.dart';
import 'operation_store.dart';

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
  @override
  State<ReceiptPage> createState() => _ReceiptPageState();
}

class _ReceiptPageState extends State<ReceiptPage> {
  final _total = TextEditingController();
  late final _amounts = [
    for (final row in widget.installments)
      TextEditingController(text: moneyInput(row['saldo_units'] as int)),
  ];
  final Set<int> _selected = {};
  bool _busy = false;
  bool _saved = false;
  String? _error;
  bool get _locked =>
      (widget.answer != null && widget.answer != 'payment') || _saved;
  bool _blocked(int i) =>
      widget.blockedIds.contains(widget.installments[i]['id']);
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

  Future<void> _confirm(String kind) async {
    if (_busy || _locked) return;
    List<Map<String, int>> payments;
    try {
      payments = kind == 'payment' ? _payments() : [];
      if (kind == 'payment' &&
          (payments.isEmpty || payments.any((p) => p['amount_units']! <= 0))) {
        throw const FormatException(
          'Marque parcelas e informe valores maiores que zero.',
        );
      }
    } on FormatException catch (e) {
      setState(() => _error = e.message);
      return;
    }
    final total = payments.fold<int>(0, (sum, p) => sum + p['amount_units']!);
    final interest = payments.fold<int>(
      0,
      (sum, p) =>
          sum +
          (p['amount_units']! > p['balance_units']!
              ? p['amount_units']! - p['balance_units']!
              : 0),
    );
    final approved = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(
          kind == 'payment' ? 'Confirmar recebimento' : 'Registrar Não pagou',
        ),
        content: Text(
          kind == 'payment'
              ? '${payments.length} parcelas selecionadas.\nTotal: ${moneyLabel(total)}\n'
                    'Inclui juros adicionais: ${moneyLabel(interest)}\n\n'
                    'O registro será salvo no aparelho, pendente de envio.'
              : 'Registrar que não houve pagamento neste contrato?'
                    '${_selected.isNotEmpty ? '\nOs valores selecionados não serão recebidos.' : ''}',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Confirmar'),
          ),
        ],
      ),
    );
    if (approved != true || !mounted) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final location = await OperationLocation().capture();
      // The active wallet must still be the one whose balances were displayed.
      final session = widget.service.session;
      final active = await widget.service.local.activeWallet(
        session.companyCode,
        '${session.userId}',
      );
      if (active != widget.walletId) {
        throw const FormatException('A carteira mudou. Reabra o contrato.');
      }
      await OperationStore(session).record(
        wallet: widget.walletId,
        client: widget.clientId,
        contracts: [widget.contractId],
        kind: kind,
        location: location,
        payments: payments,
      );
      if (mounted) {
        setState(() => _saved = true);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              location['status'] == 'timeout'
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
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              widget.clientName,
              style: Theme.of(context).textTheme.titleLarge,
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
            const SizedBox(height: 16),
            TextField(
              controller: _total,
              enabled: !_busy && !_locked,
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              decoration: const InputDecoration(
                labelText: 'Total para distribuir',
                prefixText: 'R\$ ',
                border: OutlineInputBorder(),
              ),
            ),
            Align(
              alignment: Alignment.centerRight,
              child: TextButton.icon(
                onPressed: _busy || _locked ? null : _distribute,
                icon: const Icon(Icons.call_split),
                label: const Text('Distribuir nas parcelas'),
              ),
            ),
            const Text(
              'Para acrescentar juros, edite o valor diretamente na parcela.',
            ),
            const SizedBox(height: 8),
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
                    'Obtendo GPS e salvando… Aguarde até 30 segundos pela localização.',
                  ),
                ],
              ),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: _busy || _locked || !valid
                  ? null
                  : () => _confirm('payment'),
              icon: const Icon(Icons.check),
              label: const Text('Confirmar recebimento'),
            ),
            OutlinedButton.icon(
              onPressed: _busy || _locked || widget.answer == 'payment'
                  ? null
                  : () => _confirm('unpaid'),
              icon: const Icon(Icons.thumb_down),
              label: const Text('Não pagou'),
            ),
            const Text(
              'A localização é solicitada ao confirmar. Com GPS ligado e '
              'autorizado, uma tentativa sem posição por 30 segundos permite salvar sem coordenadas.',
            ),
          ],
        ),
      ),
    );
  }

  Widget _installment(int i) {
    final row = widget.installments[i];
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    'Parcela ${row['numero']} • ${dueLabel(row['vencimento'])}',
                  ),
                ),
                Checkbox(
                  value: _selected.contains(i),
                  onChanged: _busy || _locked || _blocked(i)
                      ? null
                      : (checked) => setState(() {
                          if (checked == true) {
                            _selected.add(i);
                          } else {
                            _selected.remove(i);
                          }
                        }),
                ),
              ],
            ),
            Text('Saldo: ${moneyLabel(row['saldo_units'] as int)}'),
            if (_blocked(i))
              const Text('Recebimento pendente — confira em Recebimentos'),
            const SizedBox(height: 8),
            TextField(
              controller: _amounts[i],
              enabled: !_busy && !_locked && !_blocked(i),
              keyboardType: const TextInputType.numberWithOptions(
                decimal: true,
              ),
              decoration: const InputDecoration(
                labelText: 'Valor recebido',
                prefixText: 'R\$ ',
                border: OutlineInputBorder(),
              ),
              onChanged: (_) => setState(() {}),
            ),
          ],
        ),
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
    body: FutureBuilder<List<Map<String, Object?>>>(
      future: _rows,
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return const Center(child: Text('Falha ao ler os registros locais.'));
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
              '$kind • Contrato ${row['contract_id']}',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            Text(
              'Cliente ${row['client_id']} • ${dueLabel(row['recorded_at'])}',
            ),
            if (payments.isNotEmpty) ...[
              Text('Total: ${moneyLabel(total)}'),
              for (final p in payments)
                Text(
                  'Parcela ID ${p['parcel_id']}: ${moneyLabel(p['amount_units'] as int)}'
                  ' • Juros: ${moneyLabel(p['interest_units'] as int)}',
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
