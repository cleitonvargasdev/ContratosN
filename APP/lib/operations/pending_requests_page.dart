import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../auth/auth_api.dart';
import '../config/api_config.dart';
import 'operation_store.dart';

class PendingRequestsPage extends StatefulWidget {
  const PendingRequestsPage({super.key, required this.session});
  final AuthSession session;
  @override
  State<PendingRequestsPage> createState() => _PendingRequestsPageState();
}

class _PendingRequestsPageState extends State<PendingRequestsPage> {
  late final store = OperationStore(widget.session);
  late Future<List<Map<String, Object?>>> _rows = _load();
  String? _sending;

  Future<List<Map<String, Object?>>> _load() async => (await store.pending())
      .where((row) => row['kind'] == 'solicitation')
      .toList();

  Future<void> _send(Map<String, Object?> row) async {
    setState(() => _sending = row['id'] as String);
    try {
      final payload =
          jsonDecode(row['payload'] as String) as Map<String, dynamic>;
      final response = await http
          .post(
            ApiConfig.endpoint('solicitacoes/'),
            headers: {
              'Authorization': 'Bearer ${widget.session.accessToken}',
              'Content-Type': 'application/json',
            },
            body: jsonEncode({
              'cliente_id': row['client_id'],
              'valor_pretendido': payload['valor_pretendido'],
              'frequencia_pagamento': payload['frequencia_pagamento'],
              'numero_parcelas': payload['numero_parcelas'],
              'observacao': payload['observacao'],
            }),
          )
          .timeout(const Duration(seconds: 30));
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw StateError('Resposta inválida do servidor.');
      }
      await store.removePending(row['id'] as String);
      if (mounted) {
        setState(() => _rows = _load());
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Não foi possível enviar. A solicitação continua pendente.',
            ),
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _sending = null);
      }
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
    return Card(
      child: ListTile(
        title: Text('Cliente ${row['client_id']}'),
        subtitle: Text(
          'Valor: R\$ ${payload['valor_pretendido'] ?? ''}\n${payload['frequencia_pagamento'] ?? ''} • ${payload['numero_parcelas'] ?? ''} parcelas',
        ),
        isThreeLine: true,
        trailing: FilledButton(
          onPressed: _sending == null ? () => _send(row) : null,
          child: Text(_sending == id ? 'Enviando' : 'Enviar'),
        ),
      ),
    );
  }
}
