# App 1.2 — etapa operacional local

Implementação iniciada em 20/10/2026 a partir das [referências](referencias-app/README.md).

## Escopo desta etapa

- Menu em duas colunas, com os seis atalhos da referência.
- Lista pesquisável e filtros Restando, Todas e Fora da lista.
- Clientes com ao menos uma parcela vencida ou vencendo hoje fazem parte da lista de visitas. Os que têm somente parcelas futuras ficam em Fora da lista. Datas ausentes permanecem visíveis na lista para revisão.
- Ordem local persistente por empresa/usuário, com arrastar, setas e ação de salvar.
- Detalhes por contrato com observações, comodato e negociação.
- Recebimento local por parcela, seleção e distribuição do total por vencimento/número/ID.
- Valores armazenados em unidades inteiras de 1/10.000. Excedente digitado diretamente na parcela é separado como juros adicionais em relação ao saldo atual exportado.
- Ocorrências Não pagou por contrato e Fechado para todos os contratos do cliente.
- Indicador verde somente com pagamento em todos os contratos; resposta incompleta permanece em Restando.
- GPS com prazo de 30 segundos. Apenas timeout com localização ainda ligada e autorizada permite coordenadas nulas; a ausência e a tentativa ficam registradas.
- Banco `operacoes.sqlite` separado da carteira, com isolamento por empresa/usuário, identificação de origem e gravação atômica.
- Pendências consultáveis e removíveis mediante confirmação para correção, antes de envio.
- Recebimento pendente bloqueia repetição na mesma parcela, sem bloquear outras parcelas do contrato.
- Download bloqueado enquanto houver respostas pendentes, para preservar os movimentos.

## Limites da entrega

Esta etapa ainda não envia lotes à API. Registros locais são exibidos como **Pendentes de envio**, nunca como Enviados. Não usar para cobrança real até a integração de lotes e a validação em aparelho.

Ainda pendentes: envio/processamento/recuperação de lotes; integração de solicitações e pré-cadastro; biometria; seleção de UFs na transmissão; distinção de “atrasado” e “vencido” conforme a regra de negócio.

Ocorrências usam a mesma política de GPS dos recebimentos nesta etapa. A ordem de visitas fica no aparelho. Respostas locais não expiram automaticamente na virada do dia.

As coordenadas são da operação; não alteram automaticamente o cadastro do cliente.

## Validação

Testes automatizados cobrem cálculo monetário, distribuição, consolidação de contratos, datas de visita, duplicação, transação de Fechado, isolamento por tenant/usuário, preservação de pendências, GPS desligado, permissão negada e timeout.

Resultado em 20/10/2026: 40 testes Flutter aprovados e `flutter analyze --no-pub` sem problemas. A suíte inclui testes de widgets em larguras de 360 e 400 pixels lógicos.

APK release 1.2.0+3 gerado em `D:\PROJETOINI\APP\build\app\outputs\flutter-apk\app-release.apk`, com API `https://api.vstec.net/api/v1`, assinatura RSA 3072 validada pelo `apksigner` (esquema v2) e SHA-256 `9ea8b94406ff7fb073d029f2517b1e31c651cdac222ba2269aa78ad739edc4df`.

A versão 1.2.4+7 compacta o formulário de recebimento. Antes do envio, uma parcela marcada mantém o valor recebido, inclusive parcial, bloqueado para edição. Desmarcar restaura o saldo aberto e libera o valor; confirmar sem parcelas marcadas remove o recebimento pendente local. A lista destaca somente os números de atraso e valores vencidos em vermelho, e o detalhe do contrato mostra a observação, comodato e negociação. O total digitado fica alinhado à coluna de valores, com o botão Dividir ao lado. As legendas do resumo de cobranças usam preto.

Validação física necessária: permissões Android, GPS em ambiente interno/externo, navegação, encerramento/reabertura offline e atualização sobre o APK anterior.
