import 'package:flutter/material.dart';

import 'data/local_store.dart';
import 'auth/auth_api.dart';
import 'auth/login_page.dart';
import 'auth/session_store.dart';
import 'wallet/wallet_page.dart';

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
  void initState() { super.initState(); _restore(); }
  Future<void> _restore() async {
    try {
      final session = await SessionStore.load();
      if (mounted) setState(() => _session = session);
    } catch (_) {
      if (mounted) setState(() => _sessionError = 'Não foi possível abrir a sessão segura. Feche e abra o app novamente.');
    } finally { if (mounted) setState(() => _restoring = false); }
  }
  Future<void> _logout() async {
    try {
      await SessionStore.clear();
      if (mounted) setState(() => _session = null);
    } catch (_) {
      if (mounted) setState(() => _sessionError = 'Não foi possível encerrar a sessão segura. Reinicie o app.');
    }
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'Carteira de cobranças',
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF0755A6)),
      useMaterial3: true,
    ),
    home: _restoring ? const Scaffold(body: Center(child: CircularProgressIndicator()))
      : _sessionError != null ? Scaffold(body: Center(child: Text(_sessionError!)))
      : _session == null
      ? LoginPage(onAuthenticated: (session) => setState(() => _session = session))
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

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Carteira de cobranças'), actions: [
      if (widget.onLogout != null)
        IconButton(onPressed: widget.onLogout, tooltip: 'Sair', icon: const Icon(Icons.logout)),
    ]),
    body: FutureBuilder<void>(
      future: _initialization,
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return const Center(child: Padding(
            padding: EdgeInsets.all(24),
            child: Text('Não foi possível abrir o banco local. Feche e abra o aplicativo novamente.'),
          ));
        }
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        return ListView(
          padding: const EdgeInsets.all(20),
          children: [
            if (widget.session != null) ...[
              Text('${widget.session!.name} • Empresa ${widget.session!.companyCode.toUpperCase()}'),
              const SizedBox(height: 16),
            ],
            Text('Seu dia de cobranças', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            const Text('Consulte ou atualize sua carteira em Visitas ou Transmissão.'),
            const SizedBox(height: 24),
            _entry(context, Icons.route_outlined, 'Visitas', 'Clientes e ordem de atendimento',
                'Após a integração com a API, sua carteira de visitas ficará disponível aqui, inclusive sem internet.'),
            _entry(context, Icons.payments_outlined, 'Recebimentos', 'Parcelas e ocorrências',
                'Nenhum recebimento registrado. As telas de baixa e ocorrências serão conectadas à carteira.'),
            _entry(context, Icons.sync, 'Transmissão', 'Baixar carteira e enviar lotes',
                'O download da carteira e o envio de lotes ainda estão em preparação.'),
            _entry(context, Icons.request_page_outlined, 'Solicitações', 'Solicitações do cobrador',
                'Nenhuma solicitação registrada. Este módulo está em preparação.'),
            const SizedBox(height: 24),
            const Text('Versão inicial • Cobranças e sincronização em preparação',
                style: TextStyle(color: Colors.blueGrey)),
          ],
        );
      },
    ),
  );

  Widget _entry(BuildContext context, IconData icon, String title,
      String subtitle, String message) => Card(
    child: ListTile(
      leading: Icon(icon),
      title: Text(title),
      subtitle: Text(subtitle),
      trailing: const Icon(Icons.chevron_right),
      onTap: () => Navigator.of(context).push(MaterialPageRoute<void>(
        builder: (context) => (title == 'Visitas' || title == 'Transmissão') && widget.session != null
          ? WalletPage(session: widget.session!) : Scaffold(
          appBar: AppBar(title: Text(title)),
          body: Padding(padding: const EdgeInsets.all(24), child: Text(message)),
        ),
      )),
    ),
  );
}
