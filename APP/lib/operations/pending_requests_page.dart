import 'dart:convert';

import 'package:flutter/material.dart';

import '../auth/auth_api.dart';
import '../wallet/wallet_service.dart';
import 'operation_store.dart';

class PendingRequestsPage extends StatefulWidget {
  const PendingRequestsPage({super.key, required this.session});
  final AuthSession session;
  @override
  State<PendingRequestsPage> createState() => _PendingRequestsPageState();
}

class _PendingRequestsPageState extends State<PendingRequestsPage> {
  late final store = OperationStore(widget.session);
  late final service = WalletService(widget.session);
  late Future<List<Map<String, Object?>>> _rows = _load();
  final _sending = <String>{};
  final _errors = <String, String>{};

  Future<List<Map<String, Object?>>> _load() async {
    final rows = (await store.pending())
        .where((row) => row['kind'] == 'solicitation')
        .toList();
    final clients = await service.query('SELECT id,nome FROM clientes');
    final names = {for (final c in clients) c['id']: c['nome']};
    return [
      for (final row in rows) {...row, 'client_name': names[row['client_id']]},
    ];
  }

  Future<void> _send(Map<String, Object?> row) async {
    final id = row['id'] as String;
    if (_sending.contains(id)) return;
    setState(() {
      _sending.add(id);
      _errors.remove(id);
    });
    try {
      final payload =
          jsonDecode(row['payload'] as String) as Map<String, dynamic>;
      await service.sendSolicitation({
        'cliente_id': row['client_id'],
        'valor_pretendido': payload['valor_pretendido'],
        'frequencia_pagamento': payload['frequencia_pagamento'],
        'numero_parcelas': payload['numero_parcelas'],
        'observacao': payload['observacao'],
      });
      await store.removePending(id);
      if (mounted) {
        setState(() => _rows = _load());
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(const SnackBar(content: Text('Solicitação enviada.')));
      }
    } catch (error) {
      if (mounted) {
        setState(
          () => _errors[id] = error is WalletFailure ? error.message : 'Não foi possível concluir o envio. A solicitação continua pendente.',
        );
      }
    } finally {
      if (mounted) setState(() => _sending.remove(id));
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Solicitações pendentes')),
    body: SafeArea(
      top: false,
      child: FutureBuilder<List<Map<String, Object?>>>(
        future: _rows,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return Center(
              child: TextButton(
                onPressed: () => setState(() => _rows = _load()),
                child: const Text('Falha ao carregar. Tentar novamente'),
              ),
            );
          }
          if (!snapshot.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final rows = snapshot.data!;
          if (rows.isEmpty) {
            return const Center(
              child: Text('Nenhuma solicitação pendente de envio.'),
            );
          }
          return ListView(
            padding: const EdgeInsets.all(12),
            children: [for (final row in rows) _card(row)],
          );
        },
      ),
    ),
  );

  Widget _card(Map<String, Object?> row) {
    final payload =
        jsonDecode(row['payload'] as String) as Map<String, dynamic>;
    final id = row['id'] as String;
    final savedName = '${payload['cliente_nome'] ?? ''}'.trim();
    final name = savedName.isNotEmpty
        ? savedName
        : '${row['client_name'] ?? 'Nome indisponível'}';
    return Card(
      key: ValueKey(id),
      child: ListTile(
        title: Text(name),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Valor: R\$ ${payload['valor_pretendido'] ?? ''}\n${payload['frequencia_pagamento'] ?? ''} • ${payload['numero_parcelas'] ?? ''} parcelas',
            ),
            if (_errors[id] != null)
              Text(
                _errors[id]!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
          ],
        ),
        trailing: FilledButton(
          onPressed: _sending.contains(id) ? null : () => _send(row),
          child: Text(_sending.contains(id) ? 'Enviando' : 'Enviar'),
        ),
      ),
    );
  }
}
