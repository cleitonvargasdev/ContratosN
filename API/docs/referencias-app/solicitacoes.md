# Solicitações — pré-cadastro integrado ao sistema web

Origem: três prints enviados pelo usuário em 20/10/2026, após a tela de recebimento.
Arquivos previstos, ainda pendentes de cópia:

- `solicitacoes-lista.png`
- `solicitacoes-selecao-cliente.png`
- `solicitacoes-formulario.png`

## Requisito confirmado

O aplicativo deve permitir um pré-cadastro para que a solicitação apareça no módulo de solicitações já existente no sistema web. Integrar esse fluxo ao módulo existente.

O pré-cadastro deve permitir registrar os dados de um interessado ainda sem cadastro definitivo, além de selecionar um cliente existente. A solicitação deve seguir o fluxo de análise do sistema web; enviar uma solicitação não equivale a aprovar ou gerar um contrato.

## Telas observadas

### Lista de solicitações

Título “Solicitações”, área de listagem vazia na captura e botões “VOLTAR” e “SOLICITAR”.

### Seleção de cliente

Campo “Consultar >>>>>>”, ícone de busca, lista com nomes e endereços de clientes e botão “VOLTAR”.

### Formulário

- Empresa/nome, com controle de seleção.
- CPF/CNPJ e telefone.
- Responsável e turno de cobrança.
- Endereço, número, complemento e bairro.
- Valor solicitado, quantidade de parcelas e valor da parcela.
- Botão “ATUALIZAR MEU LOCAL” e latitude/longitude.
- Botões “VOLTAR” e “CONFIRMAR”.

Os dados pessoais exibidos são exemplos visuais e não devem ser fixados no código.

## Integração existente verificada no código

- Rotas `/api/v1/solicitacoes`: listagem, detalhe, contagem de pendentes, vínculo com cliente, conclusão com contrato e rejeição.
- Controller: `app/controllers/solicitation_controller.py`.
- Schemas: `app/schemas/solicitation.py`.
- Serviço: `app/services/solicitation_service.py`.
- Repositório: `app/repositories/solicitation_repository.py`.
- Entidade `Solicitacao`: `app/models/whatsapp_chatbot.py`, já utilizada pelo chatbot.
- Tela web: `FRONTEND/src/views/solicitations/SolicitationsListView.vue`, com ações para criar cliente, criar contrato e analisar a solicitação.

O controller verificado ainda não oferece uma rota de criação de solicitação pelo app. O pré-cadastro sugerido de cliente exposto nos schemas contém nome, CPF/CNPJ e contatos; endereço, responsável, turno e GPS apresentados nesta referência precisam de mapeamento e persistência definidos para chegarem ao web sem perda.

## Trabalho previsto para vincular o app

1. Criar o formulário de solicitação com seleção de cliente existente ou pré-cadastro.
2. Definir o contrato de criação na API, reutilizando a entidade e o fluxo de solicitações existente.
3. Associar a solicitação à empresa e ao usuário autenticados, com permissões adequadas.
4. Preservar os dados complementares do pré-cadastro para consulta e aproveitamento no cadastro web.
5. Fazer a solicitação recebida aparecer na fila de análise do módulo web.
6. Retornar identificação e estado da solicitação ao app.
7. Se houver envio offline, persistir pendências e evitar duplicação em novas tentativas.

Não reutilizar automaticamente `vendedor_id` como identificação do cobrador solicitante sem definir essa relação: o vínculo do usuário no app e o vendedor são conceitos distintos.

## Pontos a definir na implementação

- Campos obrigatórios do pré-cadastro.
- Se a solicitação é enviada imediatamente ou junto ao lote de transmissão.
- Quais solicitações e estados o cobrador pode consultar.
- Aplicação da exceção de GPS de 30 segundos também a este formulário.
- Regras de cálculo/edição de quantidade e valor das parcelas.

Este documento registra requisitos e pontos de integração; a integração mobile ainda não foi implementada.
