import 'package:flutter/material.dart';

import '../auth/auth_api.dart';
import '../operations/operation_store.dart';
import '../operations/receipt_page.dart';
import 'wallet_service.dart';

class WalletPage extends StatefulWidget {
  const WalletPage({super.key, required this.session});
  final AuthSession session;
  @override
  State<WalletPage> createState() => _WalletPageState();
}

class _WalletPageState extends State<WalletPage> {
  late final service = WalletService(widget.session);
  bool _busy = false;
  String _message = 'Atualize sua carteira para trabalhar offline.';
  int? _pending;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final count = (await OperationStore(widget.session).pending()).length;
      if (mounted) setState(() => _pending = count);
    } catch (_) {
      if (mounted) {
        setState(
          () => _message = 'Não foi possível consultar as pendências locais.',
        );
      }
    }
  }

  Future<void> _download() async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final pending = await OperationStore(widget.session).pending();
      if (!mounted) return;
      if (pending.isNotEmpty) {
        final confirmed = await showDialog<bool>(
          context: context,
          barrierDismissible: false,
          builder: (context) => AlertDialog(
            title: const Text('Apagar pendências e baixar carteira?'),
            content: Text(
              'Existem ${pending.length} registros ainda não enviados. '
              'Ao substituir a carteira, os recebimentos, marcações de não pagou, '
              'fechado e solicitações pendentes serão apagados. '
              'Essa exclusão não pode ser desfeita. Deseja continuar?',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('Cancelar'),
              ),
              FilledButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Apagar e baixar'),
              ),
            ],
          ),
        );
        if (confirmed != true || !mounted) return;
      }
      final cleaned = await service.download((message) {
        if (mounted) setState(() => _message = message);
      }, discardPendingIds: pending.map((row) => row['id'] as String).toSet());
      if (mounted) {
        setState(
          () => _message = cleaned
              ? 'Carteira atualizada. Consulte os clientes em Cobranças.'
              : 'Carteira instalada. Confirmação de recebimento pendente.',
        );
      }
    } on WalletFailure catch (e) {
      if (mounted) setState(() => _message = e.message);
    } catch (_) {
      if (mounted) {
        setState(
          () => _message = 'Falha ao atualizar. Sua carteira foi preservada.',
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
      await _load();
    }
  }

  Future<void> _retry() async {
    setState(() => _busy = true);
    try {
      final count = await service.retryCleanup();
      if (mounted) {
        setState(
          () => _message = count == 0
              ? 'Nenhuma confirmação pendente.'
              : 'Recebimento da carteira confirmado.',
        );
      }
    } catch (_) {
      if (mounted) {
        setState(() => _message = 'Confirmação pendente. Verifique a conexão.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _transmit() async {
    if (_busy) return;
    setState(() => _busy = true);
    try {
      final message = await service.transmitOperations();
      if (mounted) setState(() => _message = message);
    } on WalletFailure catch (e) {
      if (mounted) setState(() => _message = e.message);
    } catch (_) {
      if (mounted) setState(() => _message = 'Não foi possível transmitir agora. O lote foi preservado.');
    } finally {
      if (mounted) setState(() => _busy = false);
      await _load();
    }
  }

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: !_busy,
    child: Scaffold(
      appBar: AppBar(title: const Text('Transmissão')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Icon(Icons.sync, size: 56, color: Color(0xFF0755A6)),
          const SizedBox(height: 24),
          Text(_message, style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 16),
          if (_busy) const LinearProgressIndicator(),
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: _busy || _pending == null ? null : _download,
            icon: const Icon(Icons.download),
            label: const Text('Baixar carteira completa'),
          ),
          TextButton(
            onPressed: _busy ? null : _retry,
            child: const Text('Repetir confirmação de recebimento'),
          ),
          const Divider(height: 40),
          Text(
            '${_pending ?? '…'} respostas pendentes neste aparelho',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          const Text(
            'Envie primeiro as cobranças e ocorrências. Se a conexão cair, '
            'o mesmo lote será retomado sem duplicar recebimentos.',
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: _busy || (_pending ?? 0) == 0 ? null : _transmit,
            icon: const Icon(Icons.upload),
            label: const Text('Enviar lote'),
          ),
          OutlinedButton.icon(
            onPressed: _busy
                ? null
                : () async {
                    await Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        builder: (_) =>
                            PendingOperationsPage(session: widget.session),
                      ),
                    );
                    if (mounted) await _load();
                  },
            icon: const Icon(Icons.receipt_long),
            label: const Text('Consultar pendências'),
          ),
        ],
      ),
    ),
  );
}
