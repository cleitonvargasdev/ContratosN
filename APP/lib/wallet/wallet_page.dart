import 'package:flutter/material.dart';
import '../auth/auth_api.dart';
import 'wallet_service.dart';

String money(Object? value) => 'R\$ ${((value as num? ?? 0) / 10000).toStringAsFixed(2).replaceAll('.', ',')}';
String dateLabel(Object? value) {
  if (value == null) return 'Não informado';
  final date = '$value'.split('T').first.split('-');
  return date.length == 3 ? '${date[2]}/${date[1]}/${date[0]}' : '$value';
}

class WalletPage extends StatefulWidget {
  const WalletPage({super.key, required this.session});
  final AuthSession session;
  @override
  State<WalletPage> createState() => _WalletPageState();
}

class _WalletPageState extends State<WalletPage> {
  late final service = WalletService(widget.session);
  List<Map<String, Object?>> _clients = [];
  bool _busy = false;
  String _message = 'Carregando carteira local…';
  String _search = '';
  @override
  void initState() { super.initState(); _load(); }

  Future<void> _load() async {
    try {
      final clients = await service.query('''SELECT c.*, COUNT(DISTINCT t.id) contratos,
        COUNT(p.id) parcelas, SUM(p.saldo_units) saldo_units
        FROM clientes c JOIN contratos t ON t.cliente_id=c.id
        JOIN parcelas p ON p.contrato_id=t.id GROUP BY c.id ORDER BY c.nome,c.id''');
      final meta = await service.query("SELECT value FROM metadata WHERE key='created_at'");
      if (mounted) { setState(() {
        _clients = clients;
        _message = meta.isEmpty ? 'Nenhuma carteira baixada para este usuário.'
          : '${clients.length} clientes • Carteira de ${dateLabel(meta.first['value'])}';
      }); }
    } catch (_) {
      if (mounted) setState(() => _message = 'Não foi possível ler a carteira local. Baixe novamente.');
    }
  }

  Future<void> _download() async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final cleaned = await service.download((message) {
        if (mounted) setState(() => _message = message);
      });
      await _load();
      if (mounted) { ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(cleaned
        ? 'Carteira instalada. ZIP removido do servidor.'
        : 'Carteira instalada. Confirmação de exclusão pendente; tente confirmar quando houver conexão.'))); }
    } on WalletFailure catch (e) {
      if (mounted) setState(() => _message = e.message);
    } finally { if (mounted) setState(() => _busy = false); }
  }

  Future<void> _retry() async {
    setState(() => _busy = true);
    try {
      final count = await service.retryCleanup();
      if (mounted) setState(() => _message = count == 0 ? 'Nenhuma confirmação pendente.' : 'Recebimento confirmado. ZIP removido do servidor.');
    } catch (_) {
      if (mounted) setState(() => _message = 'Confirmação ainda pendente. Verifique a conexão e a sessão.');
    } finally { if (mounted) setState(() => _busy = false); }
  }

  @override
  Widget build(BuildContext context) => PopScope(canPop: !_busy, child: Scaffold(
    appBar: AppBar(title: const Text('Carteira e transmissão')),
    body: Column(children: [
      Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text(_message),
        const SizedBox(height: 12),
        FilledButton.icon(onPressed: _busy ? null : _download, icon: const Icon(Icons.download), label: const Text('Baixar carteira completa')),
        TextButton(onPressed: _busy ? null : _retry, child: const Text('Repetir confirmação de recebimento')),
        if (_busy) const LinearProgressIndicator(),
        TextField(enabled: !_busy, decoration: const InputDecoration(labelText: 'Pesquisar cliente', prefixIcon: Icon(Icons.search)),
          onChanged: (value) => setState(() => _search = value.toLowerCase())),
      ])),
      Expanded(child: ListView(children: [
        for (final client in _clients.where((c) => '${c['nome']}'.toLowerCase().contains(_search)))
          ListTile(title: Text('${client['nome'] ?? 'Sem nome'}'),
            subtitle: Text('${client['endereco'] ?? ''} ${client['numero'] ?? ''}\n${client['contratos']} contratos • ${client['parcelas']} parcelas em aberto'),
            trailing: Text(money(client['saldo_units'])),
            onTap: _busy ? null : () => Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => ContractPage(service: service, client: client)))),
      ])),
    ]),
  ));
}

class ContractPage extends StatefulWidget {
  const ContractPage({super.key, required this.service, required this.client});
  final WalletService service;
  final Map<String, Object?> client;
  @override
  State<ContractPage> createState() => _ContractPageState();
}

class _ContractPageState extends State<ContractPage> {
  late final rows = widget.service.query('''SELECT t.id contrato_id, t.observacao, t.comodato,
    t.negociacao_id, p.numero, p.vencimento, p.saldo_units FROM contratos t
    JOIN parcelas p ON p.contrato_id=t.id WHERE t.cliente_id=? ORDER BY t.id,p.vencimento,p.numero''', [widget.client['id']]);
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: Text('${widget.client['nome'] ?? 'Contratos'}')),
    body: FutureBuilder<List<Map<String, Object?>>>(future: rows, builder: (context, snapshot) {
      if (snapshot.hasError) return const Center(child: Text('Não foi possível abrir os contratos.'));
      if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
      final contracts = <Object?, List<Map<String, Object?>>>{};
      for (final row in snapshot.data!) { contracts.putIfAbsent(row['contrato_id'], () => []).add(row); }
      return ListView(padding: const EdgeInsets.all(16), children: [
        Text('Telefone: ${widget.client['celular'] ?? widget.client['telefone'] ?? 'Não informado'}'),
        Text('Bairro: ${widget.client['bairro'] ?? ''} • Turno: ${widget.client['turno_cobranca'] ?? ''}'),
        const SizedBox(height: 16),
        for (final entry in contracts.entries) Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Text('Contrato ${entry.key}', style: Theme.of(context).textTheme.titleMedium),
            if (entry.value.first['comodato'] == 1) const Text('Comodato'),
            if (entry.value.first['negociacao_id'] != null) Text('Negociação ${entry.value.first['negociacao_id']}'),
            Text('Observação: ${entry.value.first['observacao'] ?? 'Sem observação'}'),
            const Divider(),
            for (final row in entry.value) ListTile(contentPadding: EdgeInsets.zero,
              title: Text('Parcela ${row['numero']}'),
              subtitle: Text('Vencimento: ${dateLabel(row['vencimento'])}'),
              trailing: Text(money(row['saldo_units']))),
          ],
        ))),
        const Text('Consulta offline. Registro de recebimentos e ocorrências em preparação.'),
      ]);
    }),
  );
}
