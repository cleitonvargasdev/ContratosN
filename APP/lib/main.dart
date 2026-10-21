import 'package:flutter/material.dart';

import 'data/local_store.dart';
import 'auth/auth_api.dart';
import 'auth/login_page.dart';
import 'auth/session_store.dart';
import 'wallet/wallet_page.dart';
import 'operations/collection_pages.dart';
import 'operations/pending_requests_page.dart';
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
    // Keep every route above Android system navigation controls.
    builder: (context, child) => SafeArea(
      top: false,
      child: child ?? const SizedBox.shrink(),
    ),
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
      page = ClientsPage(
        session: session,
        consultationOnly: title == 'Clientes',
      );
    } else if (title == 'Envio') {
      page = PendingRequestsPage(session: session);
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
            title == 'Envio'
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
      title: Row(
        children: [
          Image.asset('assets/branding/app_icon.png', width: 28, height: 28),
          const SizedBox(width: 8),
          const Text('Contratos'),
        ],
      ),
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
            'Envio',
            Icons.request_page_outlined,
            'Solicitações pendentes',
          ),
          ('Transmissão', Icons.sync, 'Atualizar sua carteira'),
          ('Configuração', Icons.settings_outlined, 'Conta e aplicativo'),
          ('Clientes', Icons.people_outline, 'Solicitações'),
          ('Encerrar', Icons.logout, 'Sair da conta'),
        ];
        return Column(
          children: [
            Container(
              height: 70,
              width: double.infinity,
              padding: EdgeInsets.zero,
              decoration: BoxDecoration(
                color: const Color(0xFF0755A6),
                image: const DecorationImage(
                  image: AssetImage('assets/branding/header.png'),
                  fit: BoxFit.cover,
                  opacity: 0.85,
                ),
              ),
              child: const Align(
                alignment: Alignment.bottomLeft,
                child: Padding(
                  padding: EdgeInsets.all(8),
                  child: Text(
                    'Ver.: 1.019',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ),
            ),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(20),
              child: LayoutBuilder(
                builder: (context, constraints) => GridView.count(
                physics: const NeverScrollableScrollPhysics(),
                crossAxisCount: 2,
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: ((constraints.maxWidth - 12) / 2) /
                    ((constraints.maxHeight - 24) / 3),
                children: [
                  for (final entry in entries)
                    Card(
                        margin: EdgeInsets.zero,
                        clipBehavior: Clip.antiAlias,
                        child: InkWell(
                          onTap: () => entry.$1 == 'Encerrar'
                              ? _exit()
                              : _open(entry.$1),
                          child: Padding(
                            padding: const EdgeInsets.all(8),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Icon(
                                  entry.$2,
                                  size: 28,
                                  color: const Color(0xFF0755A6),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  entry.$1,
                                  style: Theme.of(context)
                                      .textTheme
                                      .titleMedium,
                                ),
                              ],
                            ),
                          ),
                        ),
                    ),
                ],
                ),
              ),
            ),
            ),
            SizedBox(
              height: 55,
              width: double.infinity,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  Opacity(
                    opacity: 0.85,
                    child: Image.asset(
                      'assets/branding/footer.png',
                      fit: BoxFit.cover,
                      alignment: Alignment.bottomCenter,
                    ),
                  ),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      child: Text(
                        widget.session?.name ?? 'Cobrador',
                        style: const TextStyle(
                          color: Colors.white,
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                        ),
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
}
