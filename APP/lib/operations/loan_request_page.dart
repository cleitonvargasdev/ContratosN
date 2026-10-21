import 'package:flutter/material.dart';

import '../auth/auth_api.dart';
import '../wallet/wallet_service.dart';
import 'operation_store.dart';

class LoanRequestPage extends StatefulWidget {
  const LoanRequestPage({
    super.key,
    required this.session,
    required this.client,
  });
  final AuthSession session;
  final Map<String, Object?> client;
  @override
  State<LoanRequestPage> createState() => _LoanRequestPageState();
}

class _LoanRequestPageState extends State<LoanRequestPage> {
  final _amount = TextEditingController();
  final _installments = TextEditingController();
  final _notes = TextEditingController();
  String _frequency = 'Semanal';
  bool _saving = false;

  @override
  void dispose() {
    _amount.dispose();
    _installments.dispose();
    _notes.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    final amount = double.tryParse(
      _amount.text.replaceAll('.', '').replaceAll(',', '.'),
    );
    if (amount == null || amount <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Informe o valor pretendido.')),
      );
      return;
    }
    setState(() => _saving = true);
    try {
      final service = WalletService(widget.session);
      final wallet = await service.local.activeWallet(
        widget.session.companyCode,
        '${widget.session.userId}',
      );
      if (wallet == null) {
        throw const FormatException(
          'Baixe a carteira antes de registrar solicitações.',
        );
      }
      await OperationStore(widget.session).record(
        wallet: wallet,
        client: widget.client['id'] as int,
        contracts: [-(widget.client['id'] as int)],
        kind: 'solicitation',
        location: {'status': 'not_required'},
        payments: const [],
        extra: {
          'valor_pretendido': amount,
          'frequencia_pagamento': _frequency,
          'numero_parcelas': int.tryParse(_installments.text),
          'observacao': _notes.text.trim().isEmpty ? null : _notes.text.trim(),
        },
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Solicitação salva para envio no lote.')),
      );
      Navigator.pop(context);
    } on FormatException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(e.message)));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Nova solicitação')),
    body: SafeArea(
      top: false,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            '${widget.client['nome'] ?? 'Cliente'}',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          Text(
            '${widget.client['celular'] ?? widget.client['telefone'] ?? ''}',
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _amount,
            keyboardType: const TextInputType.numberWithOptions(decimal: true),
            decoration: const InputDecoration(
              labelText: 'Valor pretendido',
              prefixText: 'R\$ ',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            initialValue: _frequency,
            decoration: const InputDecoration(
              labelText: 'Frequência',
              border: OutlineInputBorder(),
            ),
            items: const [
              DropdownMenuItem(value: 'Semanal', child: Text('Semanal')),
              DropdownMenuItem(value: 'Quinzenal', child: Text('Quinzenal')),
              DropdownMenuItem(value: 'Mensal', child: Text('Mensal')),
            ],
            onChanged: _saving ? null : (v) => setState(() => _frequency = v!),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _installments,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'Número de parcelas',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _notes,
            maxLines: 3,
            decoration: const InputDecoration(
              labelText: 'Observação',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 20),
          FilledButton(
            onPressed: _saving ? null : _save,
            child: Text(_saving ? 'Salvando…' : 'Concluir e colocar no lote'),
          ),
        ],
      ),
    ),
  );
}
