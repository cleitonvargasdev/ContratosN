import 'dart:convert';

import 'package:flutter/material.dart';

import '../auth/auth_api.dart';
import '../wallet/wallet_service.dart';
import 'collection_rules.dart';
import 'operation_store.dart';
import 'receipt_page.dart';
import 'location_service.dart';

String dueLabel(Object? value) {
  final parts = '${value ?? ''}'.split('T').first.split('-');
  return parts.length == 3 ? '${parts[2]}/${parts[1]}/${parts[0]}' : 'Sem data';
}

String statusLabel(VisitStatus status) => switch (status) {
  VisitStatus.pending => 'A visitar',
  VisitStatus.partial => 'Atendimento parcial',
  VisitStatus.partialUnpaid => 'Não pagou • Atendimento parcial',
  VisitStatus.paid => 'Todos os contratos pagos',
  VisitStatus.unpaid => 'Não pagou',
  VisitStatus.closed => 'Fechado',
};

IconData statusIcon(VisitStatus status) => switch (status) {
  VisitStatus.paid => Icons.check_circle,
  VisitStatus.unpaid || VisitStatus.partialUnpaid => Icons.thumb_down,
  VisitStatus.closed => Icons.store_mall_directory_outlined,
  _ => Icons.schedule,
};

Color statusColor(VisitStatus status) => switch (status) {
  VisitStatus.paid => Colors.green.shade800,
  VisitStatus.unpaid ||
  VisitStatus.partialUnpaid ||
  VisitStatus.closed => Colors.red.shade800,
  _ => Colors.blueGrey,
};

class ClientSummary {
  ClientSummary(this.data);
  final Map<String, Object?> data;
  final Set<int> contracts = {};
  int balance = 0;
  int overdueBalance = 0;
  int overdueCount = 0;
  bool due = false;
  VisitStatus status = VisitStatus.pending;
  int get id => data['id'] as int;
}

class ClientsPage extends StatefulWidget {
  const ClientsPage({super.key, required this.session});
  final AuthSession session;
  @override
  State<ClientsPage> createState() => _ClientsPageState();
}

class _ClientsPageState extends State<ClientsPage> {
  late final service = WalletService(widget.session);
  late final store = OperationStore(widget.session);
  List<ClientSummary> _clients = [];
  String _search = '';
  int _filter = 0;
  bool _loading = true;
  bool _ordering = false;
  bool _saving = false;
  String? _error;
  final _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final rows = await service.query('''SELECT c.*, t.id AS contract_id,
        p.saldo_units,p.vencimento FROM clientes c
        JOIN contratos t ON t.cliente_id=c.id JOIN parcelas p ON p.contrato_id=t.id
        ORDER BY c.nome,c.id,t.id,p.vencimento,p.numero,p.id''');
      final wallet = await service.local.activeWallet(
        widget.session.companyCode,
        '${widget.session.userId}',
      );
      final answers = await store.answers(wallet ?? '');
      final order = await store.order();
      final map = <int, ClientSummary>{};
      final today = DateTime.now();
      for (final row in rows) {
        final c = map.putIfAbsent(row['id'] as int, () => ClientSummary(row));
        c.contracts.add(row['contract_id'] as int);
        final balance = row['saldo_units'] as int;
        c.balance += balance;
        c.due |= dueByToday(row['vencimento'], today);
        if (overdue(row['vencimento'], today)) {
          c.overdueCount++;
          c.overdueBalance += balance;
        }
      }
      final clients = map.values.toList();
      for (final c in clients) {
        c.status = visitStatus(c.contracts.map((id) => answers[id]).toList());
      }
      clients.sort((a, b) {
        final comparison = (order[a.id] ?? 2147483647).compareTo(
          order[b.id] ?? 2147483647,
        );
        if (comparison != 0) return comparison;
        final name = '${a.data['nome']}'.compareTo('${b.data['nome']}');
        return name != 0 ? name : a.id.compareTo(b.id);
      });
      if (mounted) setState(() => _clients = clients);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Não foi possível abrir a carteira.');
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  bool _matches(ClientSummary c, int filter) => switch (filter) {
    0 => c.due && !visitComplete(c.status),
    1 => c.due,
    _ => !c.due,
  };

  Future<void> _saveOrder() async {
    setState(() => _saving = true);
    try {
      await store.saveOrder(_clients.map((c) => c.id).toList());
      if (mounted) {
        setState(() => _ordering = false);
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Ordem de visitas salva neste aparelho.'),
          ),
        );
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Falha ao salvar a ordem. Tente novamente.'),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final visible = _ordering
        ? _clients
        : _clients
              .where(
                (c) =>
                    _matches(c, _filter) &&
                    '${c.data['nome']} ${c.data['endereco']} ${c.data['bairro']}'
                        .toLowerCase()
                        .contains(_search),
              )
              .toList();
    return PopScope(
      canPop: !_ordering && !_saving,
      child: Scaffold(
        appBar: AppBar(
          title: Text(_ordering ? 'Organizar visitas' : 'Clientes'),
          actions: [
            if (!_ordering)
              IconButton(
                tooltip: 'Organizar ordem completa',
                icon: const Icon(Icons.sort),
                onPressed: _loading || _clients.isEmpty
                    ? null
                    : () => setState(() {
                        _ordering = true;
                        _search = '';
                        _searchController.clear();
                      }),
              ),
          ],
        ),
        body: _loading
            ? const Center(child: CircularProgressIndicator())
            : _error != null
            ? Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(_error!),
                    TextButton(
                      onPressed: _load,
                      child: const Text('Tentar novamente'),
                    ),
                  ],
                ),
              )
            : Column(
                children: [
                  if (!_ordering)
                    Padding(
                      padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
                      child: TextField(
                        controller: _searchController,
                        decoration: const InputDecoration(
                          prefixIcon: Icon(Icons.search),
                          hintText: 'Nome, endereço ou bairro',
                          border: OutlineInputBorder(),
                        ),
                        onChanged: (value) => setState(
                          () => _search = value.toLowerCase().trim(),
                        ),
                      ),
                    ),
                  if (!_ordering)
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      child: Wrap(
                        spacing: 6,
                        runSpacing: 4,
                        children: [
                          for (var i = 0; i < 3; i++)
                            ChoiceChip(
                              selected: _filter == i,
                              label: Text(
                                '${['Restando', 'Todas', 'Fora'][i]} '
                                '(${_clients.where((c) => _matches(c, i)).length})',
                              ),
                              onSelected: (_) => setState(() => _filter = i),
                            ),
                        ],
                      ),
                    ),
                  if (_ordering)
                    const Padding(
                      padding: EdgeInsets.all(16),
                      child: Text(
                        'Ordem completa, sem filtros. Arraste pelo ícone ou use as setas.',
                      ),
                    ),
                  Expanded(
                    child: visible.isEmpty
                        ? Center(
                            child: Padding(
                              padding: const EdgeInsets.all(24),
                              child: Text(
                                _clients.isEmpty
                                    ? 'Nenhuma carteira disponível. Baixe em Transmissão.'
                                    : 'Nenhum cliente nesta seleção.',
                              ),
                            ),
                          )
                        : _ordering
                        ? ReorderableListView.builder(
                            buildDefaultDragHandles: false,
                            itemCount: visible.length,
                            onReorderItem: (old, next) {
                              if (_saving) return;
                              setState(() {
                                _clients.insert(next, _clients.removeAt(old));
                              });
                            },
                            itemBuilder: (context, index) => ListTile(
                              key: ValueKey(visible[index].id),
                              title: Text('${visible[index].data['nome']}'),
                              leading: Text('${index + 1}'),
                              trailing: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  IconButton(
                                    tooltip: 'Mover para cima',
                                    onPressed: _saving || index == 0
                                        ? null
                                        : () => setState(() {
                                            _clients.insert(
                                              index - 1,
                                              _clients.removeAt(index),
                                            );
                                          }),
                                    icon: const Icon(Icons.arrow_upward),
                                  ),
                                  IconButton(
                                    tooltip: 'Mover para baixo',
                                    onPressed:
                                        _saving || index == _clients.length - 1
                                        ? null
                                        : () => setState(() {
                                            _clients.insert(
                                              index + 1,
                                              _clients.removeAt(index),
                                            );
                                          }),
                                    icon: const Icon(Icons.arrow_downward),
                                  ),
                                  ReorderableDragStartListener(
                                    index: index,
                                    enabled: !_saving,
                                    child: const Padding(
                                      padding: EdgeInsets.all(12),
                                      child: Icon(Icons.drag_handle),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          )
                        : RefreshIndicator(
                            onRefresh: _load,
                            child: ListView.builder(
                              physics: const AlwaysScrollableScrollPhysics(),
                              padding: const EdgeInsets.all(12),
                              itemCount: visible.length,
                              itemBuilder: (context, index) =>
                                  _card(visible[index]),
                            ),
                          ),
                  ),
                  if (_ordering)
                    SafeArea(
                      top: false,
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Row(
                          children: [
                            TextButton(
                              onPressed: _saving
                                  ? null
                                  : () {
                                      setState(() => _ordering = false);
                                      _load();
                                    },
                              child: const Text('Cancelar'),
                            ),
                            const Spacer(),
                            FilledButton(
                              onPressed: _saving ? null : _saveOrder,
                              child: Text(
                                _saving ? 'Salvando…' : 'Salvar ordem',
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                ],
              ),
      ),
    );
  }

  Widget _card(ClientSummary c) {
    final address = [
      '${c.data['endereco'] ?? ''}'.trim(),
      if ('${c.data['numero'] ?? ''}'.trim().isNotEmpty)
        'N.º ${c.data['numero']}',
    ].where((part) => part.isNotEmpty).join(' ');
    final place = [
      '${c.data['bairro'] ?? ''}'.trim(),
      '${c.data['cidade'] ?? ''}'.trim(),
    ].where((part) => part.isNotEmpty).join(' • ');
    final phone = '${c.data['celular'] ?? c.data['telefone'] ?? ''}'.trim();

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: () async {
          await Navigator.of(context).push(
            MaterialPageRoute<void>(
              builder: (_) => ClientContractsPage(service: service, client: c),
            ),
          );
          if (mounted) await _load();
        },
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 9, 12, 10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      '${c.data['nome'] ?? 'Sem nome'}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleMedium
                          ?.copyWith(fontWeight: FontWeight.w700),
                    ),
                  ),
                  Icon(
                    visitComplete(c.status)
                        ? statusIcon(c.status)
                        : Icons.chevron_right,
                    size: 18,
                    color: visitComplete(c.status)
                        ? statusColor(c.status)
                        : Colors.black87,
                  ),
                ],
              ),
              if (address.isNotEmpty)
                Text(address, maxLines: 1, overflow: TextOverflow.ellipsis),
              if (place.isNotEmpty)
                Text(place, maxLines: 1, overflow: TextOverflow.ellipsis),
              const SizedBox(height: 5),
              _summaryRow('C:', '', 'F:', phone, rightValueColor: Colors.black),
              const SizedBox(height: 4),
              _summaryRow(
                'CONTRATOS:',
                '${c.contracts.length}',
                'TURNO COB.:',
                '${c.data['turno_cobranca'] ?? ''}',
                leftValueColor: Colors.blue.shade800,
                rightValueColor: Colors.black,
              ),
              const SizedBox(height: 4),
              _summaryRow(
                'PARC. ATRASO:',
                '${c.overdueCount}',
                'VALOR',
                moneyLabel(c.overdueBalance),
                leftValueColor: Colors.red.shade800,
                rightValueColor: Colors.red.shade800,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _summaryRow(
    String leftLabel,
    String leftValue,
    String rightLabel,
    String rightValue, {
    Color? leftValueColor,
    Color? rightValueColor,
  }) => Row(
    children: [
      Expanded(
        child: RichText(
          text: TextSpan(
            style: DefaultTextStyle.of(context).style.copyWith(fontSize: 12),
            children: [
              TextSpan(
                text: '$leftLabel ',
                style: const TextStyle(color: Colors.black),
              ),
              TextSpan(
                text: leftValue,
                style: TextStyle(
                  color: leftValueColor,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ),
      Expanded(
        child: RichText(
          textAlign: TextAlign.right,
          text: TextSpan(
            style: DefaultTextStyle.of(context).style.copyWith(fontSize: 12),
            children: [
              TextSpan(
                text: '$rightLabel ',
                style: const TextStyle(color: Colors.black),
              ),
              TextSpan(
                text: rightValue,
                style: TextStyle(
                  color: rightValueColor,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ),
    ],
  );
}

class ClientContractsPage extends StatefulWidget {
  const ClientContractsPage({
    super.key,
    required this.service,
    required this.client,
  });
  final WalletService service;
  final ClientSummary client;
  @override
  State<ClientContractsPage> createState() => _ClientContractsPageState();
}

class _ClientContractsPageState extends State<ClientContractsPage> {
  late final store = OperationStore(widget.service.session);
  Map<int, List<Map<String, Object?>>> _contracts = {};
  Map<int, String> _answers = {};
  Map<int, Set<int>> _blocked = {};
  Map<int, Map<int, int>> _pendingPayments = {};
  String? _wallet;
  bool _loading = true;
  bool _busy = false;
  String? _error;
  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final rows = await widget.service.query(
        '''SELECT t.id AS contract_id,
        t.observacao,t.comodato,t.negociacao_id,p.* FROM contratos t
        JOIN parcelas p ON p.contrato_id=t.id WHERE t.cliente_id=?
        ORDER BY t.id,p.vencimento,p.numero,p.id''',
        [widget.client.id],
      );
      final session = widget.service.session;
      _wallet = await widget.service.local.activeWallet(
        session.companyCode,
        '${session.userId}',
      );
      final answers = await store.answers(_wallet ?? '');
      final pending = await store.pending();
      final blocked = <int, Set<int>>{};
      final pendingPayments = <int, Map<int, int>>{};
      for (final row in pending.where((r) => r['wallet_id'] == _wallet)) {
        final payload =
            jsonDecode(row['payload'] as String) as Map<String, dynamic>;
        for (final p in payload['payments'] as List) {
          final parcelId = p['parcel_id'] as int;
          blocked
              .putIfAbsent(row['contract_id'] as int, () => <int>{})
              .add(parcelId);
          if (row['kind'] == 'payment') {
            pendingPayments
                .putIfAbsent(row['contract_id'] as int, () => <int, int>{})
                .putIfAbsent(parcelId, () => p['amount_units'] as int);
          }
        }
      }
      final contracts = <int, List<Map<String, Object?>>>{};
      for (final r in rows) {
        contracts.putIfAbsent(r['contract_id'] as int, () => []).add(r);
      }
      if (mounted) {
        setState(() {
          _contracts = contracts;
          _answers = answers;
          _blocked = blocked;
          _pendingPayments = pendingPayments;
          _loading = false;
          _error = null;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = 'Não foi possível abrir os contratos.';
          _loading = false;
        });
      }
    }
  }

  Future<void> _closed() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Cliente fechado?'),
        content: const Text(
          'Registrar Fechado para todos os contratos deste cliente?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Registrar'),
          ),
        ],
      ),
    );
    if (confirm != true || !mounted) return;
    setState(() => _busy = true);
    try {
      final location = await OperationLocation().capture();
      await store.record(
        wallet: _wallet!,
        client: widget.client.id,
        contracts: _contracts.keys.toList(),
        kind: 'closed',
        location: location,
      );
      await _load();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              location['status'] == 'timeout'
                  ? 'Fechado salvo. GPS sem posição após 30 segundos.'
                  : 'Fechado salvo. Pendente de envio.',
            ),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              e is LocationFailure
                  ? e.message
                  : 'Não foi possível registrar Fechado.',
            ),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: !_busy,
    child: Scaffold(
      appBar: AppBar(
        title: Text('${widget.client.data['nome'] ?? 'Contratos'}'),
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
          ? Center(child: Text(_error!))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Text(
                  'Telefone: ${widget.client.data['celular'] ?? widget.client.data['telefone'] ?? 'Não informado'}',
                ),
                const SizedBox(height: 12),
                for (final entry in _contracts.entries)
                  _contract(entry.key, entry.value),
                const SizedBox(height: 16),
                FilledButton.tonalIcon(
                  onPressed:
                      _busy ||
                          _wallet == null ||
                          _contracts.isEmpty ||
                          _contracts.keys.any(_answers.containsKey)
                      ? null
                      : _closed,
                  icon: const Icon(Icons.store_mall_directory_outlined),
                  label: const Text('Cliente fechado — todos os contratos'),
                ),
                if (_contracts.keys.any(_answers.containsKey))
                  const Text(
                    'Para corrigir respostas pendentes, abra Recebimentos no menu.',
                  ),
                if (_busy)
                  const Padding(
                    padding: EdgeInsets.all(16),
                    child: Column(
                      children: [
                        LinearProgressIndicator(),
                        Text('Obtendo localização… até 30 segundos.'),
                      ],
                    ),
                  ),
              ],
            ),
    ),
  );

  Widget _contract(int id, List<Map<String, Object?>> rows) {
    final now = DateTime.now();
    final late = rows.where((r) => overdue(r['vencimento'], now)).toList();
    final total = rows.fold<int>(
      0,
      (sum, r) => sum + (r['saldo_units'] as int),
    );
    final answer = _answers[id];
    return Card(
      child: ListTile(
        contentPadding: const EdgeInsets.all(16),
        title: Text('Contrato $id'),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 8),
            Text(
              '${late.length} parcelas em atraso • ${moneyLabel(total)} em aberto',
            ),
            Text(
              late.isEmpty ? 'Em dia' : 'Com parcelas em atraso',
              style: TextStyle(
                color: late.isEmpty
                    ? Colors.green.shade800
                    : Colors.orange.shade900,
              ),
            ),
            Text(
              'OBSERVAÇÃO: ${'${rows.first['observacao'] ?? ''}'.trim().isEmpty ? 'Não informada' : rows.first['observacao']}',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            if (rows.first['comodato'] == 1) const Text('COMODATO: Sim'),
            if (rows.first['negociacao_id'] != null)
              Text('NEGOCIAÇÃO: ${rows.first['negociacao_id']}'),
            if (answer != null)
              Text(
                '${switch (answer) {
                  'payment' => 'Recebimento registrado',
                  'unpaid' => 'Não pagou',
                  _ => 'Fechado',
                }} • Pendente de envio',
              ),
          ],
        ),
        trailing: answer == null
            ? const Icon(Icons.chevron_right)
            : Icon(
                answer == 'payment'
                    ? Icons.check_circle
                    : answer == 'unpaid'
                    ? Icons.thumb_down
                    : Icons.store_mall_directory_outlined,
                color: answer == 'payment'
                    ? Colors.green.shade800
                    : answer == 'unpaid'
                    ? Colors.red.shade800
                    : Colors.blue.shade800,
              ),
        onTap: _busy
            ? null
            : () async {
                await Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => ReceiptPage(
                      service: widget.service,
                      clientId: widget.client.id,
                      clientName: '${widget.client.data['nome']}',
                      contractId: id,
                      walletId: _wallet!,
                      installments: rows,
                      answer: answer,
                      blockedIds: _blocked[id] ?? {},
                      pendingPayments: _pendingPayments[id] ?? {},
                    ),
                  ),
                );
                if (mounted) await _load();
              },
      ),
    );
  }
}
