# Transmissão — carteira e recebimentos

Origem: segundo print enviado pelo usuário em 20/10/2026.
Arquivo previsto: `transmissao.png` nesta pasta, ainda pendente de cópia.

## Finalidade confirmada pelo usuário

Tela onde o cobrador baixa a carteira e envia os recebimentos realizados no período.

## Elementos observados

- Tela vertical com fundo cinza muito claro e banner “CONTRATOS” no topo.
- Texto “Andamento do Processo” seguido de uma barra de progresso horizontal.
- Instrução para selecionar um ou mais estados e clicar em “Receber”. O botão visível correspondente está rotulado “BAIXAR”.
- Lista de siglas de estados à esquerda. Estão visíveis AC, AL, AP, AM, BA, CE, DF, ES, GO, MA, MT e MS. O print não permite concluir se essa é a lista completa.
- Dois botões à direita, dispostos verticalmente: “BAIXAR” com ícone de transferência e “ENVIAR” com ícone de envelope.
- Indicador inferior “ESTADOS Nenhum”, representando a seleção exibida na captura.
- Acesso “MENU >>>” no canto inferior direito, acompanhado de um ícone de menu.

## Modelo operacional para a construção

| Ação | Função |
| --- | --- |
| Selecionar estados | Permitir seleção de uma ou mais UFs para o download da carteira, conforme a instrução visível. |
| Baixar | Obter a carteira do usuário autenticado. |
| Enviar | Transmitir os recebimentos realizados no período, conforme explicado pelo usuário. |
| Menu | Acesso ao menu do aplicativo; destino exato a confirmar durante a implementação. |

O vínculo da carteira permanece pelo usuário responsável pelo cliente (`clientes.usuario_id`). O filtro de estados complementa esse vínculo.

## Diferenças em relação ao código atual

- A carga atual exporta a carteira inteira do usuário, sem filtro de UF. A seleção de estados desta referência ainda precisa ser implementada.
- O download e a instalação local da carteira já existem.
- O registro e o envio de recebimentos ainda precisam ser implementados; o botão ilustrado não representa uma funcionalidade já pronta no novo app.

## Pontos ainda não definidos pela imagem

- Comportamento de “Baixar” quando nenhum estado está selecionado.
- Se a seleção de estados também restringe o envio ou somente o download.
- Como o período dos recebimentos é definido. Não há seletor de datas visível; não presumir filtro por data.
- Quais confirmações e mensagens aparecem após sucesso, falha ou envio parcial.

Consultar também as regras de sincronização e preservação de movimentos pendentes no [documento de migração](../app-cobrador-migracao.md).
