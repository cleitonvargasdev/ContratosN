/// Endereço único: a empresa é enviada no login e preservada pelo JWT.
class ApiConfig {
  static const baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://api.vstec.net/api/v1',
  );

  static Uri endpoint(String relativePath) {
    final base = Uri.parse(baseUrl);
    if (base.scheme != 'https' || base.host.isEmpty ||
        base.userInfo.isNotEmpty || base.hasQuery || base.hasFragment) {
      throw StateError('Configure uma URL HTTPS válida para a API.');
    }
    return base.replace(path: '${base.path.replaceFirst(RegExp(r'/+$'), '')}/${relativePath.replaceFirst(RegExp(r'^/+'), '')}');
  }
}
