import 'package:flutter/material.dart';
import 'auth_api.dart';
import 'session_store.dart';

class LoginPage extends StatefulWidget {
  const LoginPage({super.key, required this.onAuthenticated, this.api});
  final ValueChanged<AuthSession> onAuthenticated;
  final AuthApi? api;

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _form = GlobalKey<FormState>();
  final _company = TextEditingController();
  final _user = TextEditingController();
  final _password = TextEditingController();
  bool _loading = false;
  bool _hidePassword = true;
  String? _error;

  @override
  void dispose() {
    _company.dispose();
    _user.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_loading || !_form.currentState!.validate()) return;
    FocusScope.of(context).unfocus();
    setState(() { _loading = true; _error = null; });
    try {
      final session = await (widget.api ?? AuthApi()).login(
        _company.text, _user.text, _password.text);
      if (!mounted) return;
      await SessionStore.save(session);
      if (!mounted) return;
      _password.clear();
      widget.onAuthenticated(session);
    } on AuthFailure catch (failure) {
      if (mounted) setState(() => _error = failure.message);
    } catch (_) {
      if (mounted) setState(() => _error = 'Não foi possível entrar. Tente novamente.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Carteira de cobranças')),
    body: Center(child: ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 480),
      child: SingleChildScrollView(padding: const EdgeInsets.all(24),
        child: Form(key: _form, child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(20),
              child: SizedBox(
                height: 190,
                child: Image.asset(
                  'assets/branding/opening.png',
                  fit: BoxFit.cover,
                  alignment: Alignment.topCenter,
                ),
              ),
            ),
            const SizedBox(height: 24),
            Text('Entre na sua empresa', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            const Text('Use o código da empresa e seu usuário cadastrado. É necessário estar conectado para entrar.'),
            const SizedBox(height: 24),
            TextFormField(controller: _company, enabled: !_loading,
              decoration: const InputDecoration(labelText: 'Código da empresa', hintText: 'Ex.: cv, ms ou bc', border: OutlineInputBorder()),
              autocorrect: false, enableSuggestions: false,
              textInputAction: TextInputAction.next,
              validator: (v) => v == null || v.trim().isEmpty ? 'Informe o código da empresa.' : null),
            const SizedBox(height: 16),
            TextFormField(controller: _user, enabled: !_loading,
              decoration: const InputDecoration(labelText: 'Usuário', border: OutlineInputBorder()),
              autocorrect: false, enableSuggestions: false,
              textInputAction: TextInputAction.next,
              validator: (v) => v == null || v.trim().isEmpty ? 'Informe o usuário.' : null),
            const SizedBox(height: 16),
            TextFormField(controller: _password, enabled: !_loading,
              obscureText: _hidePassword, autocorrect: false, enableSuggestions: false,
              decoration: InputDecoration(labelText: 'Senha', border: const OutlineInputBorder(),
                suffixIcon: IconButton(onPressed: _loading ? null : () => setState(() => _hidePassword = !_hidePassword),
                  tooltip: _hidePassword ? 'Mostrar senha' : 'Ocultar senha',
                  icon: Icon(_hidePassword ? Icons.visibility_outlined : Icons.visibility_off_outlined))),
              textInputAction: TextInputAction.done,
              onFieldSubmitted: (_) => _submit(),
              validator: (v) => v == null || v.isEmpty ? 'Informe a senha.' : null),
            if (_error != null) Padding(padding: const EdgeInsets.only(top: 16),
              child: Semantics(liveRegion: true, child: Text(_error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error)))),
            const SizedBox(height: 24),
            FilledButton(onPressed: _loading ? null : _submit,
              child: Padding(padding: const EdgeInsets.all(12),
                child: Text(_loading ? 'Entrando…' : 'Entrar'))),
          ],
        )),
      ),
    )),
  );
}
