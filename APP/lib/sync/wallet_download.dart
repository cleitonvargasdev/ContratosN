/// Contrato do fluxo. Os adaptadores de arquivos, validação e HTTP ainda serão
/// implementados quando o formato da carteira e as rotas da API forem definidos.
abstract interface class WalletDownloadPort {
  Future<void> downloadAndValidate(String downloadId);
  Future<void> installValidatedWallet(String downloadId);
  Future<void> persistPendingConfirmation(String downloadId);
  Future<void> confirmReceiptAndDeleteRemoteZip(String downloadId);
  Future<void> removePendingConfirmation(String downloadId);
}

enum WalletDownloadResult { installed, installedCleanupPending }

class WalletDownload {
  const WalletDownload(this.port);
  final WalletDownloadPort port;

  Future<WalletDownloadResult> execute(String downloadId) async {
    await port.downloadAndValidate(downloadId);
    await port.installValidatedWallet(downloadId);
    await port.persistPendingConfirmation(downloadId);
    // Uma falha aqui não invalida a carteira instalada. A confirmação deve
    // continuar pendente e ser repetida, com a mesma identidade autenticada.
    try {
      await retryConfirmation(downloadId);
      return WalletDownloadResult.installed;
    } catch (_) {
      return WalletDownloadResult.installedCleanupPending;
    }
  }

  Future<void> retryConfirmation(String downloadId) async {
    await port.confirmReceiptAndDeleteRemoteZip(downloadId);
    await port.removePendingConfirmation(downloadId);
  }
}
