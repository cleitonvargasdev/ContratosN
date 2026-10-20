import 'package:flutter/material.dart';

import 'data/local_store.dart';
import 'auth/auth_api.dart';
import 'auth/login_page.dart';
import 'auth/session_store.dart';
import 'wallet/wallet_page.dart';
import 'operations/collection_pages.dart';
import 'operations/receipt_page.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const CobradorApp());
}

class CobradorApp extends StatefulWidget {
  const CobradorApp({super.key});

  @override
  State<CobradorApp> createState() => _CobradorAppState();
}

class _CobradorAppState extends State<CobradorApp> {
  AuthSession? _session;
  bool _restoring = true;
  String? _sessionError;
  @override
  void initState() {
    super.initState();
    _restore();
  }

  Future<void> _restore() async {
    try {
      final session = await SessionStore.load();
      if (mounted) setState(() => _session = session);
    } catch (_) {
      if (mounted) {
        setState(
          () => _sessionError = 'Não foi possível abrir a sessão segura. Feche e abra o app novamente.',
        );
      }
    } finally {
      if (mounted) setState(() => _restoring = false);
    }
  }

  Future<void> _logout() async {
    try {
      await SessionStore.clear();
      if (mounted) setState(() => _session = null);
    } catch (_) {
      if (mounted) {
        setState(
          () => _sessionError =
              'Não foi possível encerrar a sessão segura. Reinicie o app.',
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'Carteira de cobranças',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0755A6)),
      useMaterial3: true,
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(2)),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(2)),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(2)),
        ),
      ),
    ),
    home: _restoring
        ? const Scaffold(body: Center(child: CircularProgressIndicator()))
        : _sessionError != null
        ? Scaffold(body: Center(child: Text(_sessionError!)))
        : _session == null
        ? LoginPage(
            onAuthenticated: (session) => setState(() => _session = session),
          )
        : HomePage(session: _session, onLogout: _logout),
  );
}

class HomePage extends StatefulWidget {
  const HomePage({super.key, this.initialize, this.session, this.onLogout});
  final Future<void> Function()? initialize;
  final AuthSession? session;
  final VoidCallback? onLogout;
  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  late final Future<void> _initialization =
      (widget.initialize ?? LocalStore.instance.initialize)();

  void _open(String title) {
    final session = widget.session;
    final Widget page;
    if (session == null) {
      page = const Scaffold(
        body: Center(child: Text('Entre para acessar sua carteira.')),
      );
    } else if (title == 'Cobranças' || title == 'Clientes') {
      page = ClientsPage(session: session);
    } else if (title == 'Transmissão') {
      page = WalletPage(session: session);
    } else if (title == 'Recebimentos') {
      page = PendingOperationsPage(session: session);
    } else {
      page = Scaffold(
        appBar: AppBar(title: Text(title)),
        body: Padding(
          padding: const EdgeInsets.all(24),
          child: Text(
            title == 'Solicitações'
                ? 'O pré-cadastro será integrado ao módulo de solicitações do sistema web.'
                : 'Empresa: ${session.companyCode.toUpperCase()}\nUsuário: ${session.name}\n'
                      'A sessão fica salva com segurança neste aparelho.\nVersão 1.2.0',
          ),
        ),
      );
    }
    Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => page));
  }

  Future<void> _exit() async {
    final exit = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Sair da conta?'),
        content: const Text(
          'A carteira e os movimentos ficam preservados neste aparelho. '
          'Será necessário entrar novamente para acessar esta conta.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Sair'),
          ),
        ],
      ),
    );
    if (exit == true) widget.onLogout?.call();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(
      title: const Text('Contratos'),
      actions: [
        IconButton(
          tooltip: 'Recebimentos e ocorrências',
          onPressed: () => _open('Recebimentos'),
          icon: const Icon(Icons.receipt_long_outlined),
        ),
      ],
    ),
    body: FutureBuilder<void>(
      future: _initialization,
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return const Center(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: Text(
                'Não foi possível abrir o banco local. Feche e abra o aplicativo novamente.',
              ),
            ),
          );
        }
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        const entries = [
          ('Cobranças', Icons.payments_outlined, 'Sua rota de atendimento'),
          (
            'Solicitações',
            Icons.request_page_outlined,
            'Pré-cadastro e propostas',
          ),
          ('Transmissão', Icons.sync, 'Atualizar sua carteira'),
          ('Configuração', Icons.settings_outlined, 'Conta e aplicativo'),
          ('Clientes', Icons.people_outline, 'Consulta da carteira'),
          ('Encerrar', Icons.logout, 'Sair da conta'),
        ];
        return ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFF0755A6),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Seu dia de cobranças',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    widget.session?.name ?? 'Carteira do cobrador',
                    style: const TextStyle(color: Colors.white),
                  ),
                  if (widget.session != null)
                    Text(
                      'Empresa ${widget.session!.companyCode.toUpperCase()}',
                      style: const TextStyle(color: Colors.white70),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            LayoutBuilder(
              builder: (context, constraints) => Wrap(
                spacing: 12,
                runSpacing: 12,
                children: [
                  for (final entry in entries)
                    SizedBox(
                      width: (constraints.maxWidth - 12) / 2,
                      child: Card(
                        margin: EdgeInsets.zero,
                        clipBehavior: Clip.antiAlias,
                        child: InkWell(
                          onTap: () => entry.$1 == 'Encerrar'
                              ? _exit()
                              : _open(entry.$1),
                          child: Padding(
                            padding: const EdgeInsets.all(20),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(
                                  entry.$2,
                                  size: 32,
                                  color: const Color(0xFF0755A6),
                                ),
                                const SizedBox(height: 16),
                                Text(
                                  entry.$1,
                                  style: Theme.of(context)
                                      .textTheme
                                      .titleMedium,
                                ),
                                const SizedBox(height: 4),
                                Text(entry.$3),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              onPressed: () => _open('Recebimentos'),
              icon: const Icon(Icons.receipt_long),
              label: const Text('Recebimentos e ocorrências pendentes'),
            ),
          ],
        );
      },
    ),
  );
}
