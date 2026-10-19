# Aplicativo do cobrador — 1.1.0+2

Flutter para Android, com carteira SQLite gerada na API e movimentações locais em banco separado.

## Disponível nesta versão

- Login por código da empresa, usuário e senha em `https://api.vstec.net/api/v1`.
- Sessão salva no armazenamento seguro do Android, sem senha, para reabrir offline. Sair remove a sessão; operações online sempre passam pela validação da API.
- Download completo da carteira do cobrador, com verificação de SHA-256, integridade SQLite, esquema, empresa e usuário.
- Consulta offline de clientes, contratos, observações, comodato/negociação e parcelas com saldo em aberto, incluindo parciais e a vencer.
- Confirmação após instalação para excluir o ZIP do servidor; confirmação pendente persistida para repetir em caso de falha.
- Renovação do token ao receber 401 nas operações da carteira.

A API atual ainda exige permissão `acesso_web`. A carteira considera `usuario_id_vendedor` do contrato como cobrador. Administrador sem contratos atribuídos recebe carteira vazia.

## Ainda pendente

Registro de recebimentos, ocorrências, GPS de visitas, solicitações, ordenação web de rotas e envio/processamento de lotes. Esta versão permite testar login e carteira; ainda não substitui o aplicativo operacional de cobrança.

## Compilar e validar

SDK Flutter: `D:\PROJETOINI\flutter-sdk`. Android SDK: `D:\PROJETOINI\android-sdk`. JDK: `C:\Program Files\Java\jdk-21`.

```powershell
D:\PROJETOINI\flutter-sdk\bin\flutter.bat analyze
D:\PROJETOINI\flutter-sdk\bin\flutter.bat test
.\scripts\build-production.ps1
```

O script configura temporariamente o Java para usar os certificados confiáveis do Windows, necessários para baixar dependências neste ambiente, e restaura a variável depois. Não desativa validação TLS.

APK: `build/app/outputs/flutter-apk/app-release.apk`. Assinatura própria em `android/signing/cobrador-release.jks`, configuração em `android/key.properties`, ambos ignorados pelo Git. Manter backup privado desses arquivos para assinar futuras atualizações.

## Implantação e teste

Atualizar a API conforme `../API/docs/app-carteira-sqlite.md` antes de testar o novo download. Instalar o APK sobre o anterior, entrar com usuário de teste autorizado, abrir Visitas ou Transmissão e baixar a carteira. Conferir os contratos/observações, ativar modo avião, fechar/reabrir e consultar novamente. Nenhuma baixa financeira é realizada nesta versão.

Dados de carteira e confirmações são segregados por empresa e usuário. Banco SQLite de carteira: esquema 1, valores inteiros na escala 10.000. Banco de movimentações: esquema 2, com ponteiro de carteira ativa e confirmações pendentes, sem tabelas de pagamentos ainda.

Os testes incluem fixture ZIP gerada pelo serviço Python da API (somente dados fictícios), instalada em SQLite real no teste desktop. O comportamento no aparelho e com dados reais deve ser validado após a implantação.
