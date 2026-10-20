# Contratos do cliente

Origem: quarto print enviado pelo usuário em 20/10/2026.
Arquivo previsto: `contratos-cliente.png` nesta pasta, ainda pendente de cópia.

## Comportamento confirmado pelo usuário

Ao tocar em um cliente na lista, o aplicativo apresenta seus dados separados por contrato, com legendas de situação. Nesta tela, o cobrador pode marcar o cliente como “Fechado”.

A marcação “Fechado” se refere ao cliente e vale para todos os seus contratos, conforme confirmação em 20/10/2026. Não interpretar como encerramento, cancelamento ou quitação de contrato.

## Elementos observados

- Título “Contratos do Cliente”.
- Um cartão por contrato, com nome do cliente, número do contrato, quantidade de parcelas em atraso e valor em atraso.
- No exemplo, o mesmo cliente tem dois contratos: um com uma parcela em atraso e outro com zero parcelas em atraso.
- Faixa colorida no resumo de cada contrato.
- Legenda próxima ao rodapé:
  - Verde: “EM DIAS”.
  - Amarelo: “ATRASADO”.
  - Vermelho: “VENCIDO”.
- Botão verde “ATUALIZAR MEU LOCAL”, com ícone de atualização.
- Campos “LAT.” e “LONG.” mostrando coordenadas.
- Botão vermelho “FECHADO”.
- Botão azul “OK” com ícone de retorno.

As coordenadas e os dados pessoais do exemplo não devem ser usados como dados fixos na implementação.

## Orientação para a construção

- Manter a separação por contrato e apresentar os valores com clareza.
- Usar texto ou ícone junto às cores para permitir identificar a situação sem depender apenas da cor.
- Preservar a ação de registrar “Fechado” no contexto do cliente.
- Tratar ocorrência de visita e situação financeira como informações distintas.
- Compatibilizar o registro de ocorrências com o funcionamento offline e a sincronização, conforme as regras gerais da migração.

## Pontos ainda não definidos

- Critério que diferencia “Atrasado” de “Vencido”; não deduzir apenas pela cor.
- Critério adotado no desenvolvimento: “Fechado” responde todos os contratos e conclui a visita, retirando o cliente de “Restando”.
- Se “Fechado” exige confirmação, observação ou captura automática de localização.
- Se “Atualizar meu local” registra a localização da visita ou altera as coordenadas do cadastro do cliente.
- Destino do botão “OK” e comportamento ao tocar em um contrato.

Consultar a [tela de clientes](clientes.md) e o [documento de migração](../app-cobrador-migracao.md).
