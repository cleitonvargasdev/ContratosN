<template>
  <section class="panel form-panel contract-form-panel">
    <div class="contract-tabs" role="tablist" aria-label="Abas do contrato">
      <button class="contract-tabs__button" :class="{ 'contract-tabs__button--active': activeTab === 'dados' }" type="button" @click="activeTab = 'dados'">
        Dados do contrato
      </button>
      <button class="contract-tabs__button" :class="{ 'contract-tabs__button--active': activeTab === 'parcelas' }" type="button" @click="activeTab = 'parcelas'">
        Parcelas
      </button>
    </div>

    <form class="contract-form" @submit.prevent="submitForm">
      <section v-if="activeTab === 'dados'" class="contract-tab-panel">
        <div class="contract-form__cards">
          <section class="contract-card contract-card--main">
            <header class="contract-card__header">
              <div>
                <h3 class="panel__title">Informações Gerais</h3>
              </div>
              <span class="contract-status-caption" :class="form.quitado ? 'contract-status-caption--paid' : 'contract-status-caption--open'">
                {{ form.quitado ? 'Quitado' : 'Aberto' }}
              </span>
            </header>

            <div class="contract-card__grid">
              <label class="field-group">
                <span>Nº Contrato</span>
                <div class="field-inline contract-number-field" :class="{ 'contract-number-field--with-action': hasNegotiatedContracts }">
                  <input v-model="form.contratos_id" :disabled="contractEditLocked" class="field field--no-spin" required type="number" />
                  <button
                    v-if="hasNegotiatedContracts"
                    class="contract-number-field__action"
                    type="button"
                    title="Contratos Negociados"
                    aria-label="Contratos Negociados"
                  >
                    <svg viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M3 6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v3h-7a3 3 0 0 0 0 6h7v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6Zm11 5a1 1 0 1 0 0 2h7v-2h-7Z" fill="currentColor" />
                    </svg>
                  </button>
                </div>
              </label>

              <label class="field-group">
                <span>Data Lançto.</span>
                <input v-model="form.data_lancto" class="field field--readonly" readonly type="datetime-local" />
              </label>

              <label class="field-group">
                <span>Data Contrato</span>
                <input v-model="form.data_contrato" :disabled="contractEditLocked" class="field" type="datetime-local" />
              </label>

              <label class="field-group">
                <span>Data Final</span>
                <input v-model="form.data_final" class="field field--readonly" readonly type="datetime-local" />
              </label>

              <label class="field-group field-group--span-2">
                <span>Cliente</span>
                <div class="field-inline contract-client-picker">
                  <input :value="selectedClientLabel" class="field field--readonly contract-client-picker__field" readonly type="text" />
                  <button
                    class="secondary-button contract-client-picker__button"
                    :aria-disabled="contractEditLocked"
                    :class="{ 'secondary-button--disabled': contractEditLocked }"
                    title="Consultar cliente"
                    aria-label="Consultar cliente"
                    type="button"
                    @click="openClientModal"
                  >
                    <svg class="contract-client-picker__icon" viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M10.5 4a6.5 6.5 0 1 0 4.03 11.6l4.44 4.44 1.41-1.41-4.44-4.44A6.5 6.5 0 0 0 10.5 4Zm0 2a4.5 4.5 0 1 1 0 9 4.5 4.5 0 0 1 0-9Z" fill="currentColor" />
                    </svg>
                  </button>
                </div>
              </label>

              <label class="field-group field-group--span-2">
                <span>Vendedor</span>
                <select v-model.number="form.usuario_id_vendedor" :disabled="contractEditLocked" class="field">
                  <option :value="null">Selecione</option>
                  <option v-for="user in sellerOptions" :key="user.id" :value="user.id">
                    {{ user.nome }}
                  </option>
                </select>
              </label>

              <label class="field-group field-group--span-2">
                <span>OBS</span>
                <textarea v-model="form.obs" :readonly="contractEditLocked" class="field field--textarea contract-obs-textarea" rows="2"></textarea>
              </label>

              <div class="contract-financials-grid field-group field-group--span-2">
                <label class="field-group">
                  <span>Valor Recebido</span>
                  <input v-model="form.valor_recebido" class="field field--readonly contract-financial-field contract-financial-field--received" readonly type="text" />
                </label>

                <label class="field-group">
                  <span>Valor Aberto</span>
                  <input v-model="form.valor_em_aberto" class="field field--readonly contract-financial-field contract-financial-field--open" readonly type="text" />
                </label>

                <label class="field-group">
                  <span>Valor em Atraso</span>
                  <input v-model="form.valor_em_atraso" class="field field--readonly contract-financial-field contract-financial-field--overdue" readonly type="text" />
                </label>
              </div>
            </div>
          </section>

          <section class="contract-card">
            <header class="contract-card__header">
              <div>
                <h3 class="panel__title">Plano e Valores</h3>
              </div>
            </header>

            <div class="contract-card__grid">
              <label class="field-group field-group--span-2">
                <span>Plano de Pagamento</span>
                <select v-model.number="form.plano_id" :disabled="contractEditLocked" class="field" @change="syncPlanDefaults">
                  <option :value="null">Selecione</option>
                  <option v-for="plan in paymentPlans" :key="plan.plano_id" :value="plan.plano_id">
                    {{ plan.descricao || `Plano ${plan.plano_id}` }}
                  </option>
                </select>
              </label>

              <div class="contract-card__triple field-group field-group--span-2">
                <label class="field-group">
                  <span>Valor empréstimo</span>
                  <input v-model="form.valor_empretismo" :readonly="contractEditLocked" class="field" inputmode="decimal" type="text" @blur="formatDecimalField('valor_empretismo')" />
                </label>

                <label class="field-group">
                  <span>Dias</span>
                  <input v-model="form.qtde_dias" :readonly="contractEditLocked" class="field" inputmode="numeric" type="text" @input="handleDaysInput" />
                </label>

                <label class="field-group">
                  <span>Valor Parcela</span>
                <input v-model="form.valor_parcela" :readonly="contractEditLocked" class="field" inputmode="decimal" type="text" @input="handleInstallmentValueInput" @blur="formatDecimalField('valor_parcela')" />
              </label>
              </div>

              <label class="field-group">
                <span>Valor Final</span>
                <input v-model="form.valor_final" :readonly="contractEditLocked" class="field" inputmode="decimal" type="text" @input="handleFinalValueInput" @blur="formatDecimalField('valor_final')" />
              </label>

              <label class="field-group">
                <span>Juros % a.m</span>
                <input v-model="form.percent_juros" :readonly="contractEditLocked" class="field" inputmode="decimal" type="text" @blur="formatDecimalField('percent_juros')" />
              </label>

              <label class="field-group field-group--span-2">
                <span>Regra de Juros</span>
                <select v-model.number="form.regra_juros_id" class="field">
                  <option :value="null">Selecione</option>
                  <option v-for="rule in regraJurosOptions" :key="rule.regra_juros_id" :value="rule.regra_juros_id">
                    {{ rule.descricao || `Regra ${rule.regra_juros_id}` }}
                  </option>
                </select>
              </label>

              <label class="field-group field-group--span-2">
                <span>Regra Comissão</span>
                <select v-model.number="form.regra_comissao_id" class="field">
                  <option :value="null">Selecione</option>
                  <option v-for="rule in regraComissaoOptions" :key="rule.regra_comissao_id" :value="rule.regra_comissao_id">
                    {{ rule.descricao || `Regra ${rule.regra_comissao_id}` }}
                  </option>
                </select>
              </label>

              <div class="field-group field-group--span-2 contract-days-picker">
                <span>Dias em que realiza cobrança</span>
                <div class="contract-days-picker__grid">
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.sabado" :disabled="contractEditLocked" type="checkbox" />
                    <span>Sábado</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.domingo" :disabled="contractEditLocked" type="checkbox" />
                    <span>Domingo</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.feriado" :disabled="contractEditLocked" type="checkbox" />
                    <span>Feriado</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.mensal" :disabled="contractEditLocked" type="checkbox" @change="handleMonthlyBillingChange" />
                    <span>Mensal</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.quinzenal" :disabled="contractEditLocked" type="checkbox" @change="handleBiweeklyBillingChange" />
                    <span>Quinzenal</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.segunda" :disabled="contractEditLocked" type="checkbox" />
                    <span>Segunda</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.terca" :disabled="contractEditLocked" type="checkbox" />
                    <span>Terça</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.quarta" :disabled="contractEditLocked" type="checkbox" />
                    <span>Quarta</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.quinta" :disabled="contractEditLocked" type="checkbox" />
                    <span>Quinta</span>
                  </label>
                  <label class="contract-days-picker__item">
                    <input v-model="billingDays.sexta" :disabled="contractEditLocked" type="checkbox" />
                    <span>Sexta</span>
                  </label>
                  <label class="contract-days-picker__item contract-days-picker__item--recorrente">
                    <input v-model="form.recorrencia" :disabled="contractEditLocked" type="checkbox" @change="handleRecurringChange" />
                    <span class="contract-days-picker__label--recorrente">Recorrente - valor dos juros se repete</span>
                  </label>
                  <label class="contract-days-picker__item contract-days-picker__item--aluguel">
                    <input v-model="form.aluguel" :disabled="contractEditLocked" type="checkbox" @change="handleRentChange" />
                    <span class="contract-days-picker__label--recorrente">Aluguel</span>
                  </label>
                </div>
              </div>
            </div>
          </section>
        </div>

      </section>

      <section v-else class="contract-tab-panel">
        <div class="contract-installments">
          <section class="contract-card contract-card--parcelas">
            <header class="contract-card__header contract-card__header--parcelas">
              <div>
                <h3 class="panel__title">Parcelas</h3>
                <p class="contract-card__subtitle">{{ installmentsCaptionLabel }}</p>
              </div>
              <div v-if="props.mode === 'edit'" class="contract-installments__header-actions">
                <button
                  class="ghost-button ghost-button--danger primary-button--compact contract-installments__bulk-settle-button"
                  :disabled="installmentsSaving || !currentContractId || openInstallmentsCount === 0"
                  type="button"
                  @click="handleSettleAllInstallments"
                >
                  Quitar todas
                </button>
                <button
                  class="primary-button primary-button--accent-soft primary-button--compact contract-installments__add-button"
                  :disabled="installmentsSaving"
                  type="button"
                  @click="openInstallmentCreateModal"
                >
                  Incluir Parcela +
                </button>
              </div>
            </header>

            <div class="contract-installments__tools">
              <span v-if="installmentsLoading" class="feedback feedback--info contract-installments__status">Atualizando parcelas...</span>
            </div>

            <div class="table-wrap contract-installments__table-wrap">
              <table class="data-table contract-installments__table">
                <thead>
                  <tr>
                    <th>Parc.</th>
                    <th>Vencimento</th>
                    <th>Dia Semana</th>
                    <th>Atraso</th>
                    <th>Valor</th>
                    <th>Juros</th>
                    <th>Valor Total</th>
                    <th>Vl. Recebido</th>
                    <th>Pgto</th>
                    <th>Quitar</th>
                    <th>Del</th>
                    <th>ALT</th>
                    <th>Msg</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!installmentsLoading && installmentRows.length === 0">
                    <td colspan="13">Nenhuma parcela gerada.</td>
                  </tr>
                  <tr v-for="row in installmentRows" :key="row.key" :class="{ 'contract-installments__row--paid': row.isPaid }">
                    <td>{{ row.label }}</td>
                    <td class="contract-installments__action-cell">
                      <span class="contract-installments__due-date" :class="{ 'contract-installments__due-date--overdue': row.isOverdue }">{{ row.dueDate }}</span>
                    </td>
                    <td>{{ row.weekday }}</td>
                    <td>{{ row.overdueDays }}</td>
                    <td>{{ row.baseValue }}</td>
                    <td>{{ row.interestValue }}</td>
                    <td>{{ row.value }}</td>
                    <td>{{ row.receivedValue }}</td>
                    <td class="contract-installments__action-cell">
                      <button class="contract-installments__action contract-installments__action--pay" :disabled="!row.canPay || installmentsSaving" type="button" title="Receber parcela" aria-label="Receber parcela" @click="handleReceiveInstallment(row.id)">
                        <span class="contract-installments__action-icon" aria-hidden="true">
                          <svg viewBox="0 0 24 24">
                            <path d="M3 6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v3H3V6Zm0 5h18v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7Zm4 3v2h4v-2H7Z" fill="currentColor" />
                          </svg>
                        </span>
                      </button>
                    </td>
                    <td class="contract-installments__action-cell">
                      <button class="contract-installments__action contract-installments__action--settle" :disabled="!row.canSettle || installmentsSaving" type="button" :title="row.settleTitle" :aria-label="row.settleTitle" @click="handleSettleInstallment(row.id)">
                        <span class="contract-installments__action-icon" aria-hidden="true">
                          <svg viewBox="0 0 24 24">
                            <path d="M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" fill="currentColor" />
                          </svg>
                        </span>
                      </button>
                    </td>
                    <td class="contract-installments__action-cell">
                      <button class="contract-installments__action contract-installments__action--delete" :disabled="!row.canDeletePayment || installmentsSaving" type="button" title="Excluir pagamento" aria-label="Excluir pagamento" @click="handleDeleteInstallmentPayment(row.id)">
                        <span class="contract-installments__action-icon" aria-hidden="true">
                          <svg viewBox="0 0 24 24">
                            <path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor" />
                          </svg>
                        </span>
                      </button>
                    </td>
                    <td class="contract-installments__action-cell">
                      <button class="contract-installments__action contract-installments__action--edit" :disabled="!row.canEdit || installmentsSaving" type="button" title="Alterar parcela" aria-label="Alterar parcela" @click="openInstallmentEditModal(row.id)">
                        <span class="contract-installments__action-icon" aria-hidden="true">
                          <svg viewBox="0 0 24 24">
                            <path d="M3 17.25V21h3.75L17.8 9.94l-3.75-3.75L3 17.25zm2.92 2.33H5v-.92l8.06-8.06.92.92L5.92 19.58zM20.71 7.04a1.003 1.003 0 0 0 0-1.42l-2.34-2.34a1.003 1.003 0 0 0-1.42 0l-1.13 1.13 3.75 3.75 1.14-1.12z" fill="currentColor" />
                          </svg>
                        </span>
                      </button>
                    </td>
                    <td>
                      <button
                        :class="['icon-action', 'icon-action--message', { 'icon-action--sent': row.whatsappSent }]"
                        :disabled="row.isPaid || !canSendCurrentClientWhatsApp || installmentsSaving"
                        type="button"
                        :title="row.whatsappSent ? 'Parcela com mensagem já enviada no WhatsApp' : 'Enviar mensagem no WhatsApp'"
                        :aria-label="row.whatsappSent ? 'Parcela com mensagem já enviada no WhatsApp' : 'Enviar mensagem no WhatsApp'"
                        @click="handleSendInstallmentWhatsApp(row.id)"
                      >
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                          <path d="M17.47 14.38c-.27-.13-1.59-.78-1.84-.87-.25-.09-.43-.13-.61.13-.18.27-.7.87-.86 1.05-.16.18-.31.2-.58.07-.27-.13-1.12-.41-2.14-1.3-.79-.7-1.33-1.56-1.48-1.83-.16-.27-.02-.41.11-.54.12-.12.27-.31.4-.47.13-.16.18-.27.27-.45.09-.18.04-.34-.02-.47-.07-.13-.61-1.47-.84-2.02-.22-.53-.44-.46-.61-.47h-.52c-.18 0-.47.07-.72.34-.25.27-.95.93-.95 2.26s.97 2.62 1.11 2.8c.13.18 1.91 2.91 4.62 4.08.65.28 1.15.45 1.54.58.65.2 1.24.17 1.7.1.52-.08 1.59-.65 1.82-1.27.22-.62.22-1.15.16-1.27-.07-.12-.25-.2-.52-.34Z" fill="currentColor"/>
                          <path d="M20.52 3.48A11.8 11.8 0 0 0 12.12 0C5.6 0 .29 5.3.29 11.82c0 2.08.54 4.1 1.57 5.88L0 24l6.48-1.7a11.8 11.8 0 0 0 5.64 1.44h.01c6.52 0 11.82-5.3 11.82-11.82 0-3.16-1.23-6.13-3.43-8.44Zm-8.4 18.26h-.01a9.84 9.84 0 0 1-5.01-1.37l-.36-.21-3.85 1.01 1.03-3.75-.23-.38a9.8 9.8 0 0 1-1.5-5.22c0-5.41 4.4-9.82 9.82-9.82 2.62 0 5.08 1.02 6.93 2.88a9.74 9.74 0 0 1 2.87 6.94c0 5.41-4.41 9.82-9.82 9.82Z" fill="currentColor"/>
                        </svg>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </section>

      <div class="form-actions form-actions--contract">
        <button class="primary-button primary-button--success form-actions__button contract-action-button" :disabled="props.saving" type="button" @click="handleNew">
          <span class="contract-action-button__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M19 11H13V5h-2v6H5v2h6v6h2v-6h6z" fill="currentColor" />
            </svg>
          </span>
          <span>Novo</span>
        </button>
        <button class="primary-button primary-button--success form-actions__button contract-action-button" :disabled="props.saving" type="submit">
          <span class="contract-action-button__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M17 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7zm-5 16a3 3 0 1 1 0-6 3 3 0 0 1 0 6m3-10H5V5h10z" fill="currentColor" />
            </svg>
          </span>
          <span>{{ props.saving ? 'Salvando...' : 'Salvar' }}</span>
        </button>
        <button class="ghost-button form-actions__button contract-action-button" :disabled="props.saving" type="button" @click="emit('cancel')">
          <span class="contract-action-button__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" fill="currentColor" />
            </svg>
          </span>
          <span>Fechar</span>
        </button>
        <button class="ghost-button ghost-button--danger form-actions__button contract-action-button" :disabled="props.saving || props.mode === 'create' || !props.canDelete" type="button" @click="emit('delete')">
          <span class="contract-action-button__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M6 7h12l-1 13a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L6 7zm3 3v8h2v-8H9zm4 0v8h2v-8h-2zM9 2h6l1 2h4v2H4V4h4l1-2z" fill="currentColor" />
            </svg>
          </span>
          <span>Excluir</span>
        </button>
        <button
          v-if="props.mode === 'edit'"
          class="primary-button primary-button--accent-soft form-actions__button contract-action-button"
          :disabled="props.saving || !currentContractId"
          type="button"
          @click="handlePrintContract"
        >
          <span class="contract-action-button__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M6 2h9l5 5v4h-2V8h-4V4H8v7H6V2zm8 1.5V9h5.5L14 3.5zM6 13h12a3 3 0 0 1 3 3v4h-3v2H6v-2H3v-4a3 3 0 0 1 3-3zm2 5v2h8v-2H8zm10-2a1 1 0 1 0 0-2 1 1 0 0 0 0 2z" fill="currentColor" />
            </svg>
          </span>
          <span>Imprimir</span>
        </button>
        <button
          v-if="activeTab === 'dados'"
          class="primary-button primary-button--accent-soft form-actions__button contract-action-button contract-action-button--calculate"
          :disabled="props.saving"
          type="button"
          @click="calculateInstallments"
        >
          <span class="contract-calc-button__icon" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M7 2h10a2 2 0 0 1 2 2v16l-4-2-4 2-4-2-4 2V4a2 2 0 0 1 2-2h2Zm1 5v2h8V7H8Zm0 4v2h8v-2H8Zm0 4v2h5v-2H8Z" fill="currentColor" />
            </svg>
          </span>
          <span>Calcular dias</span>
        </button>
      </div>
    </form>

    <p v-if="props.success" class="feedback feedback--success">{{ props.success }}</p>
    <p v-if="props.error" class="feedback feedback--error">{{ props.error }}</p>

    <Teleport to="body">
      <div v-if="clientModal.open" class="modal-backdrop" @click.self="closeClientModal">
        <section class="modal-card modal-card--clients-search">
          <header class="panel__header panel__header--stacked">
            <div>
              <h3 class="panel__title">Selecionar cliente</h3>
            </div>
            <p class="modal-context">Pesquise por empresa ou CPF/CNPJ.</p>
          </header>

          <div class="modal-form">
            <label class="field-group">
              <span>Busca</span>
              <input v-model="clientModal.term" class="field" type="text" placeholder="Digite nome, documento ou endereço" />
            </label>

            <div class="contract-client-results">
              <button
                v-for="client in filteredClients"
                :key="client.clientes_id"
                class="contract-client-result"
                :class="clientScoreClass(client.score)"
                type="button"
                @click="selectClient(client.clientes_id)"
              >
                <strong>{{ client.nome || 'Sem nome' }}</strong>
                <span>{{ formatDocument(client.cpf_cnpj) }}</span>
                <small>{{ formatClientAddress(client) }}</small>
                <div class="contract-client-result__meta">
                  <small class="contract-client-result__score-link" @click.stop="handleOpenClientScoreLog(client)">
                    Score: {{ formatScore(client.score) }}
                  </small>
                  <small>Limite: {{ formatCurrency(client.limite_credito) }}</small>
                </div>
              </button>
              <p v-if="filteredClients.length === 0" class="profile-modal-list__empty">Nenhum cliente encontrado.</p>
            </div>

            <div class="form-actions">
              <button class="ghost-button" type="button" @click="closeClientModal">Fechar</button>
            </div>
          </div>
        </section>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="installmentEditModal.open" class="modal-backdrop" @click.self="closeInstallmentEditModal">
        <section class="modal-card modal-card--installment-edit">
          <header class="panel__header panel__header--stacked installment-modal__header">
            <p class="modal-context">{{ installmentEditModal.mode === 'create' ? 'Informe os dados da nova parcela e confirme em salvar.' : 'Atualize os dados desta parcela e confirme em salvar.' }}</p>
          </header>

          <div class="modal-form installment-edit-grid">
            <label class="field-group">
              <span>Parcela</span>
              <input v-model="installmentEditModal.parcelaNro" class="field field--readonly field--no-spin" readonly inputmode="numeric" type="number" min="1" />
            </label>

            <label class="field-group">
              <span>Vencimento</span>
              <input v-model="installmentEditModal.vencimento" class="field" type="date" />
            </label>

            <label class="field-group">
              <span>Valor</span>
              <input v-model="installmentEditModal.valorBase" class="field" inputmode="decimal" type="text" @input="syncInstallmentEditTotal" @blur="formatInstallmentEditField('valorBase')" />
            </label>

            <label class="field-group">
              <span>Juros</span>
              <input v-model="installmentEditModal.valorJuros" class="field field--readonly" readonly inputmode="decimal" type="text" />
            </label>

            <label class="field-group field-group--span-2">
              <span>Valor Total</span>
              <input :value="installmentEditModal.valorTotal" class="field field--readonly" readonly type="text" />
            </label>

            <div class="form-actions installment-edit-actions field-group--span-2">
              <button class="primary-button primary-button--success installment-edit-actions__button" :disabled="installmentsSaving" type="button" @click="saveInstallmentEdit">
                {{ installmentsSaving ? 'Salvando...' : installmentEditModal.mode === 'create' ? 'Incluir' : 'Salvar' }}
              </button>
              <button class="ghost-button installment-edit-actions__button" :disabled="installmentsSaving" type="button" @click="closeInstallmentEditModal">Cancelar</button>
            </div>
          </div>
        </section>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="installmentReceiveModal.open" class="modal-backdrop" @click.self="closeInstallmentReceiveModal">
        <section class="modal-card modal-card--installment-edit">
          <header class="panel__header panel__header--stacked">
            <div>
                <h3 class="panel__title installment-modal__title installment-modal__title--receive">Receber parcela</h3>
            </div>
          </header>

          <div class="modal-form installment-edit-grid">
            <label class="field-group field-group--span-2">
              <span>Valor recebido</span>
              <input v-model="installmentReceiveModal.valorRecebido" class="field" inputmode="decimal" type="text" @input="syncInstallmentReceiveInterest" @blur="formatInstallmentReceiveField('valorRecebido')" />
            </label>

            <label class="field-group field-group--span-2">
              <span>Valor Juros</span>
              <input :value="installmentReceiveModal.juros" class="field field--readonly" readonly type="text" />
            </label>

            <div class="form-actions installment-edit-actions field-group--span-2">
              <button class="primary-button primary-button--success" :disabled="installmentsSaving" type="button" @click="saveInstallmentReceive">
                {{ installmentsSaving ? 'Recebendo...' : 'Receber' }}
              </button>
              <button class="ghost-button" :disabled="installmentsSaving" type="button" @click="closeInstallmentReceiveModal">Cancelar</button>
            </div>
          </div>
        </section>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="installmentSettleModal.open" class="modal-backdrop" @click.self="closeInstallmentSettleModal">
        <section class="modal-card modal-card--installment-edit modal-card--installment-settle">
          <header class="panel__header panel__header--stacked installment-modal__header">
            <p class="modal-context">{{ installmentSettleModal.reopen ? 'Deseja reabrir esta parcela?' : 'Deseja realizar quitacao desta parcela?' }}</p>
          </header>

          <div class="modal-form">
            <div class="installment-modal__divider" aria-hidden="true"></div>
            <div class="form-actions installment-edit-actions">
              <button class="primary-button primary-button--success installment-edit-actions__button" :disabled="installmentsSaving" type="button" @click="saveInstallmentSettle">
                {{ installmentsSaving ? 'Confirmando...' : 'Sim' }}
              </button>
              <button class="ghost-button installment-edit-actions__button" :disabled="installmentsSaving" type="button" @click="closeInstallmentSettleModal">Não</button>
            </div>
          </div>
        </section>
      </div>
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'

import type { Client, RegraComissaoOption, RegraJurosOption } from '@/models/client'
import type {
  Contract,
  ContractCreateInput,
  ContractInstallment,
  ContractInstallmentGeneratePayload,
  InstallmentCreatePayload,
  InstallmentUpdatePayload,
  ContractUpdateInput,
} from '@/models/contract'
import type { CidadeOption } from '@/models/location'
import type { FeriadoOption } from '@/models/location'
import type { PaymentPlanOption } from '@/models/paymentPlan'
import type { SolicitationContractDraft } from '@/models/solicitation'
import type { User } from '@/models/user'
import {
  createContractInstallment,
  deleteReceiptPayment,
  generateContractInstallments,
  listInstallmentReceipts,
  listContractInstallments,
  printContractPdf,
  receiveContractInstallment,
  reopenContractInstallment,
  sendInstallmentWhatsAppMessage,
  settleContractInstallment,
  settleOpenContractInstallments,
  updateContractInstallment,
} from '@/services/contractService'
import { chooseReceiptToDeletePrompt, confirmActionAlert, errorAlert, infoAlert, playCashRegisterSound, showClientScoreLogPopup, successAlert } from '@/services/alertService'
import { listClientScoreLogs, listClients, listRegraComissaoOptions, listRegraJurosOptions } from '@/services/clientService'
import { listCitiesByUf, listFeriados } from '@/services/locationService'
import { listPaymentPlans } from '@/services/paymentPlanService'
import { listUsers } from '@/services/userService'

const props = defineProps<{
  mode: 'create' | 'edit'
  saving: boolean
  error: string
  success: string
  canDelete: boolean
  initialContract?: Contract | null
  initialClientId?: number | null
  initialContractDraft?: SolicitationContractDraft | null
}>()

const emit = defineEmits<{
  submit: [payload: { contract: ContractCreateInput | ContractUpdateInput; installments: ContractInstallmentGeneratePayload | null }]
  cancel: []
  delete: []
  new: []
}>()

const activeTab = ref<'dados' | 'parcelas'>('dados')
const clientOptions = ref<Client[]>([])
const paymentPlans = ref<PaymentPlanOption[]>([])
const sellerOptions = ref<User[]>([])
const regraJurosOptions = ref<RegraJurosOption[]>([])
const regraComissaoOptions = ref<RegraComissaoOption[]>([])
const persistedInstallments = ref<ContractInstallment[]>([])
const installmentsLoading = ref(false)
const installmentsSaving = ref(false)
const holidayCache = reactive<Record<string, FeriadoOption[]>>({})
const previewInstallmentsPayload = ref<ContractInstallmentGeneratePayload | null>(null)
const generatedInstallments = ref<Array<{ key: string; id: number | null; label: string; dueDate: string; overdueDays: string; weekday: string; baseValue: string; interestValue: string; value: string; receivedValue: string; canPay: boolean; canSettle: boolean; canDeletePayment: boolean; canEdit: boolean; isOverdue: boolean; settleTitle: string; isPaid: boolean; whatsappSent: boolean }>>([])
const clientModal = reactive({ open: false, term: '' })
const installmentEditModal = reactive({
  open: false,
  mode: 'edit' as 'create' | 'edit',
  installmentId: null as number | null,
  parcelaNro: '',
  vencimento: '',
  valorBase: '',
  valorJuros: '',
  valorTotal: '',
})
const installmentReceiveModal = reactive({
  open: false,
  installmentId: null as number | null,
  saldoRestante: 0,
  valorRecebido: '',
  juros: '',
})
const installmentSettleModal = reactive({
  open: false,
  installmentId: null as number | null,
  reopen: false,
})
const cityLabels = reactive<Record<number, string>>({})
const financialFieldSyncLocked = ref(false)
const billingDays = reactive({
  sabado: false,
  domingo: false,
  feriado: false,
  mensal: false,
  quinzenal: false,
  segunda: true,
  terca: true,
  quarta: true,
  quinta: true,
  sexta: true,
})

const defaultBillingDays = {
  sabado: false,
  domingo: false,
  feriado: false,
  mensal: false,
  quinzenal: false,
  segunda: true,
  terca: true,
  quarta: true,
  quinta: true,
  sexta: true,
} as const

const form = reactive({
  contratos_id: '',
  data_lancto: '',
  data_contrato: '',
  cliente_id: null as number | null,
  plano_id: null as number | null,
  qtde_dias: '',
  percent_juros: '',
  valor_empretismo: '',
  data_final: '',
  valor_final: '',
  valor_recebido: formatDecimalValue(0),
  valor_em_aberto: formatDecimalValue(0),
  valor_em_atraso: formatDecimalValue(0),
  quitado: false,
  obs: '',
  valor_parcela: '',
  user_add: null as number | null,
  contrato_status: '1',
  negociacao_id: '',
  usuario_id_vendedor: null as number | null,
  comissao_percentual: '',
  valor_comissao_previsto: '',
  valor_comissao_apurada: '',
  regra_comissao_id: null as number | null,
  regra_juros_id: '',
  aluguel: false,
  recorrencia: false,
})

const selectedClientLabel = computed(() => {
  const client = clientOptions.value.find((item) => item.clientes_id === form.cliente_id)
  if (!client) {
    return 'Não selecionado'
  }
  return `${client.clientes_id} - ${client.nome || 'Sem nome'}`
})

const selectedClientName = computed(() => {
  const client = clientOptions.value.find((item) => item.clientes_id === form.cliente_id)
  if (client?.nome?.trim()) {
    return client.nome.trim()
  }

  if (props.initialContract?.cliente_nome?.trim()) {
    return props.initialContract.cliente_nome.trim()
  }

  return 'Sem cliente'
})

const installmentsCaptionLabel = computed(() => {
  const contractNumber = form.contratos_id.trim() || '-'
  return `Parcelas - Contrato nº ${contractNumber} - ${selectedClientName.value}`
})

const canSendCurrentClientWhatsApp = computed(() => {
  const selectedClient = clientOptions.value.find((item) => item.clientes_id === form.cliente_id)
  return Boolean(selectedClient?.flag_whatsapp && selectedClient?.celular01?.trim())
})

const hasNegotiatedContracts = computed(() => Boolean(toNumberOrNull(form.negociacao_id)))
const currentContractId = computed(() => props.initialContract?.contratos_id ?? null)
const contractEditLocked = computed(() => {
  if (props.mode !== 'edit') {
    return false
  }

  if (persistedInstallments.value.some((item) => (item.valor_recebido ?? 0) > 0 || Boolean(item.quitado))) {
    return true
  }

  return (toLocaleNumberOrNull(form.valor_recebido) ?? 0) > 0 || Boolean(form.quitado)
})

const filteredClients = computed(() => {
  const term = clientModal.term.trim().toLowerCase()
  if (!term) {
    return clientOptions.value
  }

  return clientOptions.value.filter((client) => {
    const haystack = [
      client.nome ?? '',
      client.cpf_cnpj ?? '',
      client.endereco ?? '',
      client.nro ?? '',
      cityLabels[client.cidade_id ?? -1] ?? '',
      client.uf ?? '',
    ]
      .join(' ')
      .toLowerCase()

    return haystack.includes(term)
  })
})

const sortedPersistedInstallments = computed(() => [...persistedInstallments.value].sort(compareInstallments))
const openInstallmentsCount = computed(() => persistedInstallments.value.filter((item) => !item.quitado).length)

const installmentRows = computed(() => {
  if (sortedPersistedInstallments.value.length > 0) {
    return sortedPersistedInstallments.value.map((item) => ({
      key: `db-${item.id}`,
      id: item.id,
      label: String(item.parcela_nro ?? '').padStart(2, '0'),
      dueDate: formatDateLabel(item.vencimentol ?? item.vencimento_original),
      overdueDays: formatInstallmentOverdueDays(item.vencimentol ?? item.vencimento_original, item.quitado, item.valor_total, item.valor_recebido),
      weekday: formatWeekdayLabel(item.vencimentol ?? item.vencimento_original),
      baseValue: formatCurrency(item.valor_base),
      interestValue: formatCurrency(item.valor_juros),
      value: formatCurrency(item.valor_total),
      receivedValue: formatCurrency(item.valor_recebido),
      canPay: true,
      canSettle: !item.quitado || canReopenInstallment(item),
      canDeletePayment: Boolean(item.possui_pagamento),
      canEdit: !item.quitado && !Boolean(item.possui_pagamento),
      isOverdue: isInstallmentOverdue(item.vencimentol ?? item.vencimento_original, item.quitado, item.valor_total, item.valor_recebido),
      settleTitle: canReopenInstallment(item) ? 'Reabrir parcela' : 'Quitar parcela',
      isPaid: Boolean(item.quitado),
      whatsappSent: Boolean(item.msg_whatsapp),
    }))
  }

  if (generatedInstallments.value.length > 0) {
    return generatedInstallments.value
  }

  return []
})

onMounted(() => {
  resetForm()
  void loadOptions()
})

watch(
  () => props.initialContract,
  (contract) => {
    syncContractIntoForm(contract)
  },
  { immediate: true },
)

watch(
  currentContractId,
  (contractId) => {
    generatedInstallments.value = []
    if (contractId) {
      void loadInstallments(contractId)
      return
    }

    persistedInstallments.value = []
  },
  { immediate: true },
)

watch(
  () => props.initialClientId,
  (clientId) => {
    if (props.mode === 'create' && typeof clientId === 'number' && !Number.isNaN(clientId)) {
      form.cliente_id = clientId
    }
  },
  { immediate: true },
)

watch(
  () => props.initialContractDraft,
  (draft) => {
    applyInitialContractDraft(draft)
  },
  { immediate: true },
)

async function loadOptions() {
  const [clientsResponse, plansResponse, usersResponse, jurosResponse, comissaoResponse] = await Promise.all([
    listClients({ page: 1, page_size: 100, ativo: true }),
    listPaymentPlans(),
    listUsers({ page: 1, page_size: 100, ativo: true }),
    listRegraJurosOptions(),
    listRegraComissaoOptions(),
  ])

  clientOptions.value = [...clientsResponse.items]
  paymentPlans.value = plansResponse
  sellerOptions.value = [...usersResponse.items]
  regraJurosOptions.value = jurosResponse
  regraComissaoOptions.value = comissaoResponse
  await hydrateClientCities()
  if (props.mode === 'create') {
    await assignNextContractNumber()
  }
}

function syncContractIntoForm(contract?: Contract | null) {
  if (!contract) {
    if (props.mode === 'create') {
      resetForm()
    }
    return
  }

  resetBillingDays()
  form.contratos_id = String(contract.contratos_id)
  form.data_lancto = toDateTimeLocal(contract.data_lancto)
  form.data_contrato = toDateTimeLocal(contract.data_contrato)
  form.cliente_id = contract.cliente_id
  form.plano_id = contract.plano_id
  form.qtde_dias = formatIntegerValue(contract.qtde_dias)
  form.percent_juros = formatDecimalValue(contract.percent_juros)
  form.valor_empretismo = formatDecimalValue(contract.valor_empretismo)
  form.data_final = toDateTimeLocal(contract.data_final)
  form.valor_final = formatDecimalValue(contract.valor_final)
  form.valor_recebido = formatDecimalValue(contract.valor_recebido)
  form.valor_em_aberto = formatDecimalValue(contract.valor_em_aberto)
  form.valor_em_atraso = formatDecimalValue(contract.valor_em_atraso)
  form.quitado = Boolean(contract.quitado)
  form.obs = contract.obs ?? ''
  form.valor_parcela = formatDecimalValue(contract.valor_parcela)
  form.user_add = contract.user_add
  form.contrato_status = String(contract.contrato_status)
  form.negociacao_id = toStringValue(contract.negociacao_id)
  form.usuario_id_vendedor = contract.usuario_id_vendedor
  form.comissao_percentual = toStringValue(contract.comissao_percentual)
  form.valor_comissao_previsto = toStringValue(contract.valor_comissao_previsto)
  form.valor_comissao_apurada = toStringValue(contract.valor_comissao_apurada)
  form.regra_comissao_id = contract.regra_comissao_id
  form.regra_juros_id = toStringValue(contract.regra_juros_id)
  form.aluguel = Boolean(contract.aluguel)
  form.recorrencia = Boolean(contract.recorrencia)
  billingDays.sabado = Boolean(contract.cobranca_sabado)
  billingDays.domingo = Boolean(contract.cobranca_domingo)
  billingDays.feriado = Boolean(contract.cobranca_feriado)
  billingDays.mensal = Boolean(contract.cobranca_mensal)
  billingDays.quinzenal = Boolean(contract.cobranca_quinzenal)
  billingDays.segunda = Boolean(contract.cobranca_segunda)
  billingDays.terca = Boolean(contract.cobranca_terca)
  billingDays.quarta = Boolean(contract.cobranca_quarta)
  billingDays.quinta = Boolean(contract.cobranca_quinta)
  billingDays.sexta = Boolean(contract.cobranca_sexta)
  if ((form.recorrencia || form.aluguel) && !billingDays.mensal && !billingDays.quinzenal) {
    billingDays.mensal = true
  }
  previewInstallmentsPayload.value = null
  generatedInstallments.value = []
}

function resetForm() {
  resetBillingDays()
  form.contratos_id = ''
  form.data_lancto = currentDateTimeLocal()
  form.data_contrato = currentDateTimeLocal()
  form.cliente_id = props.initialClientId ?? null
  form.plano_id = null
  form.qtde_dias = ''
  form.percent_juros = ''
  form.valor_empretismo = ''
  form.data_final = ''
  form.valor_final = ''
  form.valor_recebido = formatDecimalValue(0)
  form.valor_em_aberto = formatDecimalValue(0)
  form.valor_em_atraso = formatDecimalValue(0)
  form.quitado = false
  form.obs = ''
  form.valor_parcela = ''
  form.user_add = null
  form.contrato_status = '1'
  form.negociacao_id = ''
  form.usuario_id_vendedor = null
  form.comissao_percentual = ''
  form.valor_comissao_previsto = ''
  form.valor_comissao_apurada = ''
  form.regra_comissao_id = null
  form.regra_juros_id = ''
  form.aluguel = false
  form.recorrencia = false
  activeTab.value = 'dados'
  persistedInstallments.value = []
  previewInstallmentsPayload.value = null
  generatedInstallments.value = []
  if (props.mode === 'create') {
    void assignNextContractNumber()
  }
}

function syncPlanDefaults() {
  if (contractEditLocked.value) {
    return
  }

  const selectedPlan = paymentPlans.value.find((item) => item.plano_id === form.plano_id)
  if (!selectedPlan) {
    return
  }

  form.valor_empretismo = formatDecimalValue(selectedPlan.valor_base)
  form.qtde_dias = formatIntegerValue(selectedPlan.qtde_dias)
  form.percent_juros = formatDecimalValue(selectedPlan.percent_juros)
  form.valor_parcela = formatDecimalValue(selectedPlan.valor_parcela)
  if (!form.valor_final) {
    form.valor_final = formatDecimalValue(selectedPlan.valor_final)
  }
}

function applyInitialContractDraft(draft?: SolicitationContractDraft | null) {
  if (props.mode !== 'create' || props.initialContract || !draft) {
    return
  }

  form.cliente_id = draft.cliente_id ?? props.initialClientId ?? form.cliente_id
  form.usuario_id_vendedor = draft.usuario_id_vendedor ?? form.usuario_id_vendedor
  form.plano_id = draft.plano_id ?? form.plano_id
  form.regra_juros_id = draft.regra_juros_id === null ? form.regra_juros_id : String(draft.regra_juros_id)
  form.qtde_dias = formatIntegerValue(draft.qtde_dias ?? draft.numero_parcelas)
  form.percent_juros = draft.percent_juros === null ? form.percent_juros : formatDecimalValue(draft.percent_juros)
  form.valor_empretismo = draft.valor_empretismo === null ? form.valor_empretismo : formatDecimalValue(draft.valor_empretismo)
  form.valor_parcela = draft.valor_parcela === null ? form.valor_parcela : formatDecimalValue(draft.valor_parcela)
  form.recorrencia = Boolean(draft.recorrencia)
  form.aluguel = Boolean(draft.aluguel)

  billingDays.sabado = Boolean(draft.cobranca_sabado)
  billingDays.domingo = Boolean(draft.cobranca_domingo)
  billingDays.feriado = Boolean(draft.cobranca_feriado)
  billingDays.mensal = Boolean(draft.cobranca_mensal)
  billingDays.quinzenal = Boolean(draft.cobranca_quinzenal)
  billingDays.segunda = Boolean(draft.cobranca_segunda)
  billingDays.terca = Boolean(draft.cobranca_terca)
  billingDays.quarta = Boolean(draft.cobranca_quarta)
  billingDays.quinta = Boolean(draft.cobranca_quinta)
  billingDays.sexta = Boolean(draft.cobranca_sexta)

  if (!hasSelectedBillingDays()) {
    if (draft.frequencia_pagamento === 'Mensal') {
      billingDays.mensal = true
    } else if (draft.frequencia_pagamento === 'Quinzenal') {
      billingDays.quinzenal = true
    } else {
      resetBillingDays()
    }
  }

  const installmentValue = toLocaleNumberOrNull(form.valor_parcela) ?? 0
  const installmentsCount = toIntegerOrNull(form.qtde_dias) ?? 0
  if (!form.valor_final && installmentValue > 0 && installmentsCount > 0) {
    form.valor_final = formatDecimalValue(installmentValue * installmentsCount)
  }
}

function handleInstallmentValueInput() {
  if (financialFieldSyncLocked.value || contractEditLocked.value) {
    return
  }

  const installmentValue = toLocaleNumberOrNull(form.valor_parcela)
  const periods = toIntegerOrNull(form.qtde_dias)

  financialFieldSyncLocked.value = true
  if (installmentValue === null || periods === null || periods <= 0) {
    form.valor_final = ''
  } else {
    form.valor_final = formatDecimalValue(installmentValue * periods)
  }
  financialFieldSyncLocked.value = false
}

function handleFinalValueInput() {
  if (financialFieldSyncLocked.value || contractEditLocked.value) {
    return
  }

  const finalValue = toLocaleNumberOrNull(form.valor_final)
  const periods = toIntegerOrNull(form.qtde_dias)

  if (form.valor_parcela.trim()) {
    return
  }

  financialFieldSyncLocked.value = true
  if (finalValue === null || periods === null || periods <= 0) {
    form.valor_parcela = ''
  } else {
    form.valor_parcela = formatDecimalValue(finalValue / periods)
  }
  financialFieldSyncLocked.value = false
}

function handleDaysInput() {
  if (financialFieldSyncLocked.value || contractEditLocked.value) {
    return
  }

  if (form.valor_parcela.trim()) {
    handleInstallmentValueInput()
    return
  }

  if (form.valor_final.trim()) {
    handleFinalValueInput()
  }
}

function handleMonthlyBillingChange() {
  if (contractEditLocked.value || !billingDays.mensal) {
    return
  }

  billingDays.quinzenal = false
}

function handleBiweeklyBillingChange() {
  if (contractEditLocked.value || !billingDays.quinzenal) {
    return
  }

  billingDays.mensal = false
}

function handleRecurringChange() {
  if (contractEditLocked.value || !form.recorrencia) {
    return
  }

  form.aluguel = false
  billingDays.mensal = true
  billingDays.quinzenal = false
}

function handleRentChange() {
  if (contractEditLocked.value || !form.aluguel) {
    return
  }

  form.recorrencia = false
  if (!billingDays.mensal && !billingDays.quinzenal) {
    billingDays.mensal = true
  }
}

async function calculateInstallments() {
  if (!form.cliente_id) {
    await infoAlert('Selecione o cliente antes de calcular os dias.')
    return
  }

  if (contractEditLocked.value) {
    await infoAlert('Este contrato nao pode mais ser recalculado porque ja possui recebimentos ou parcelas quitadas.')
    return
  }

  const startDate = parseLocalDateTime(form.data_contrato)
  const scheduledContract = form.recorrencia || form.aluguel
  const installmentValue = toLocaleNumberOrNull(form.valor_parcela) ?? toLocaleNumberOrNull(form.valor_final)
  const qtdDias = toIntegerOrNull(form.qtde_dias)

  if (form.recorrencia && form.aluguel) {
    await infoAlert('Aluguel e recorrente nao podem estar marcados juntos.')
    return
  }

  if (!billingDays.mensal && !billingDays.quinzenal && !hasAnyWeeklyBillingDaySelected()) {
    await infoAlert('Selecione ao menos um dia de cobranca ou uma frequencia mensal/quinzenal.')
    return
  }

  if (scheduledContract && !form.valor_parcela.trim()) {
    await infoAlert('Informe o valor da parcela para contratos de aluguel ou recorrentes.')
    return
  }

  if (!scheduledContract && !form.plano_id && (!form.valor_parcela.trim() || !form.qtde_dias.trim())) {
    await infoAlert('Selecione o plano ou informe os valores antes de calcular os dias.')
    return
  }

  if (!startDate || installmentValue === null || (!scheduledContract && (qtdDias === null || qtdDias <= 0))) {
    await infoAlert('Selecione o plano ou informe data do contrato, dias e valor antes de calcular os dias.')
    return
  }

  const holidaySet = await loadHolidaySet()
  const dueDates = scheduledContract
    ? buildSingleScheduledDueDate(startDate, holidaySet)
    : buildDueDates(startDate, qtdDias as number, holidaySet)
  const endDate = dueDates.at(-1) ?? null
  form.data_final = endDate ? toDateTimeLocal(endDate.toISOString()) : ''

  const principalValue = toLocaleNumberOrNull(form.valor_empretismo)
  const calculatedFinalValue = dueDates.length > 0 ? dueDates.length * installmentValue : null
  const monthlyInterestRate =
    endDate && principalValue !== null && principalValue > 0 && calculatedFinalValue !== null
      ? calculateMonthlyInterestRate(startDate, endDate, principalValue, calculatedFinalValue)
      : null

  form.valor_final = calculatedFinalValue === null ? '' : formatDecimalValue(calculatedFinalValue)
  form.percent_juros = monthlyInterestRate === null ? '' : formatDecimalValue(monthlyInterestRate)

  if (dueDates.length === 0) {
    previewInstallmentsPayload.value = null
    generatedInstallments.value = []
    if (persistedInstallments.value.length > 0) {
      syncFinancialTotalsFromInstallments()
    } else {
      resetFinancialTotals()
    }
    activeTab.value = 'parcelas'
    return
  }

  const payload: ContractInstallmentGeneratePayload = {
    parcelas: dueDates.map((date, index) => ({
      parcela_nro: index + 1,
      vencimento: toApiDateTimeLocal(date),
      valor_total: installmentValue,
    })),
  }

  if (!currentContractId.value) {
    previewInstallmentsPayload.value = payload
    syncFinancialTotalsFromPreview(dueDates, installmentValue)
    generatedInstallments.value = payload.parcelas.map((item) => ({
      key: `preview-${item.parcela_nro}`,
      id: null,
      label: String(item.parcela_nro).padStart(2, '0'),
      dueDate: formatDateLabel(item.vencimento),
      overdueDays: formatInstallmentOverdueDays(item.vencimento, false, item.valor_total, 0),
      weekday: formatWeekdayLabel(item.vencimento),
      baseValue: formatCurrency(item.valor_total),
      interestValue: formatCurrency(0),
      value: formatCurrency(item.valor_total),
      receivedValue: '-',
      canPay: false,
      canSettle: false,
      canDeletePayment: false,
      canEdit: false,
      isOverdue: isInstallmentOverdue(item.vencimento, false, item.valor_total, 0),
      settleTitle: 'Quitar parcela',
      isPaid: false,
      whatsappSent: false,
    }))
    activeTab.value = 'parcelas'
    return
  }

  installmentsSaving.value = true
  try {
    persistedInstallments.value = await generateContractInstallments(currentContractId.value, payload)
    previewInstallmentsPayload.value = null
    syncQuitadoFromInstallments()
    syncFinancialTotalsFromInstallments()
    generatedInstallments.value = []
    activeTab.value = 'parcelas'
    void successAlert('Parcelas geradas em contas a receber.', 'update')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao gerar parcelas do contrato')
  } finally {
    installmentsSaving.value = false
  }
}

async function handlePrintContract() {
  if (!currentContractId.value) {
    await infoAlert('Salve o contrato antes de imprimir.')
    return
  }

  try {
    const pdfBlob = await printContractPdf(currentContractId.value)
    const pdfUrl = URL.createObjectURL(pdfBlob)
    window.open(pdfUrl, '_blank', 'noopener,noreferrer')
    window.setTimeout(() => URL.revokeObjectURL(pdfUrl), 60_000)
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao imprimir contrato')
  }
}

async function loadInstallments(contractId: number) {
  installmentsLoading.value = true
  try {
    persistedInstallments.value = await listContractInstallments(contractId)
    previewInstallmentsPayload.value = null
    syncQuitadoFromInstallments()
    syncFinancialTotalsFromInstallments()
  } catch {
    persistedInstallments.value = []
  } finally {
    installmentsLoading.value = false
  }
}

async function handleReceiveInstallment(installmentId: number | null) {
  if (!installmentId) {
    return
  }

  const row = persistedInstallments.value.find((item) => item.id === installmentId)
  if (row?.quitado) {
    await infoAlert('Esta parcela ja esta quitada.')
    return
  }

  const remainingValue = row ? Math.max((row.valor_total ?? 0) - (row.valor_recebido ?? 0), 0) : null
  installmentReceiveModal.open = true
  installmentReceiveModal.installmentId = installmentId
  installmentReceiveModal.saldoRestante = remainingValue ?? 0
  installmentReceiveModal.valorRecebido = formatDecimalValue(remainingValue ?? 0) || formatDecimalValue(0)
  installmentReceiveModal.juros = formatDecimalValue(0) || formatDecimalValue(0)
  syncInstallmentReceiveInterest()
}

function closeInstallmentReceiveModal() {
  installmentReceiveModal.open = false
  installmentReceiveModal.installmentId = null
  installmentReceiveModal.saldoRestante = 0
  installmentReceiveModal.valorRecebido = ''
  installmentReceiveModal.juros = ''
}

function syncInstallmentReceiveInterest() {
  const paidValue = toLocaleNumberOrNull(installmentReceiveModal.valorRecebido) ?? 0
  const interestValue = Math.max(paidValue - installmentReceiveModal.saldoRestante, 0)
  installmentReceiveModal.juros = formatDecimalValue(interestValue) || formatDecimalValue(0)
}

function formatInstallmentReceiveField(field: 'valorRecebido') {
  const parsed = toLocaleNumberOrNull(installmentReceiveModal[field])
  installmentReceiveModal[field] = parsed === null ? '' : formatDecimalValue(parsed)
  syncInstallmentReceiveInterest()
}

async function saveInstallmentReceive() {
  if (!installmentReceiveModal.installmentId) {
    return
  }

  const valorRecebido = toLocaleNumberOrNull(installmentReceiveModal.valorRecebido)
  const juros = toLocaleNumberOrNull(installmentReceiveModal.juros)
  if (valorRecebido === null || valorRecebido <= 0) {
    await infoAlert('Informe um valor recebido maior que zero.')
    return
  }

  installmentsSaving.value = true
  try {
    await receiveContractInstallment(installmentReceiveModal.installmentId, {
      valor_recebido: valorRecebido,
      data_recebimento: currentDateTimeLocal(),
      desconto: null,
      juros,
    })
    if (currentContractId.value) {
      persistedInstallments.value = await listContractInstallments(currentContractId.value)
    }
    syncQuitadoFromInstallments()
    syncFinancialTotalsFromInstallments()
    closeInstallmentReceiveModal()
    playCashRegisterSound()
    void successAlert('Recebimento lançado com sucesso.', 'update')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao registrar recebimento')
  } finally {
    installmentsSaving.value = false
  }
}

async function handleSettleInstallment(installmentId: number | null) {
  if (!installmentId) {
    return
  }

  const installment = persistedInstallments.value.find((item) => item.id === installmentId)
  installmentSettleModal.open = true
  installmentSettleModal.installmentId = installmentId
  installmentSettleModal.reopen = installment ? canReopenInstallment(installment) : false
}

function closeInstallmentSettleModal() {
  installmentSettleModal.open = false
  installmentSettleModal.installmentId = null
  installmentSettleModal.reopen = false
}

async function saveInstallmentSettle() {
  if (!installmentSettleModal.installmentId) {
    return
  }

  const reopening = installmentSettleModal.reopen
  installmentsSaving.value = true
  try {
    const updated = reopening
      ? await reopenContractInstallment(installmentSettleModal.installmentId)
      : await settleContractInstallment(installmentSettleModal.installmentId, {
          data_recebimento: currentDateTimeLocal(),
        })
    updateInstallmentInState(updated)
    syncQuitadoFromInstallments()
    syncFinancialTotalsFromInstallments()
    closeInstallmentSettleModal()
    if (!reopening) {
      playCashRegisterSound()
    }
    void successAlert(reopening ? 'Parcela reaberta com sucesso.' : 'Parcela quitada com sucesso.', 'update')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : reopening ? 'Falha ao reabrir parcela' : 'Falha ao quitar parcela')
  } finally {
    installmentsSaving.value = false
  }
}

async function handleSettleAllInstallments() {
  if (!currentContractId.value) {
    return
  }

  if (openInstallmentsCount.value === 0) {
    await infoAlert('Nao existem parcelas em aberto para quitar.')
    return
  }

  const confirmed = await confirmActionAlert(
    'Quitar todas as parcelas?',
    'Essa acao vai marcar como quitadas todas as parcelas em aberto, mesmo sem valor recebido.',
    'Quitar todas',
  )

  if (!confirmed) {
    return
  }

  installmentsSaving.value = true
  try {
    persistedInstallments.value = await settleOpenContractInstallments(currentContractId.value, {
      data_recebimento: currentDateTimeLocal(),
    })
    syncQuitadoFromInstallments()
    syncFinancialTotalsFromInstallments()
    playCashRegisterSound()
    void successAlert('Parcelas em aberto quitadas com sucesso.', 'update')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao quitar parcelas em aberto')
  } finally {
    installmentsSaving.value = false
  }
}

function canReopenInstallment(installment: ContractInstallment) {
  if (!installment.quitado) {
    return false
  }

  return (installment.valor_recebido ?? 0) < (installment.valor_total ?? 0)
}

function openInstallmentEditModal(installmentId: number | null) {
  if (!installmentId) {
    return
  }

  const installment = persistedInstallments.value.find((item) => item.id === installmentId)
  if (!installment || installment.quitado || installment.possui_pagamento) {
    return
  }

  installmentEditModal.open = true
  installmentEditModal.mode = 'edit'
  installmentEditModal.installmentId = installment.id
  installmentEditModal.parcelaNro = String(installment.parcela_nro ?? '')
  installmentEditModal.vencimento = toDateInputValue(installment.vencimentol ?? installment.vencimento_original)
  installmentEditModal.valorBase = formatDecimalValue(installment.valor_base) || formatDecimalValue(0)
  installmentEditModal.valorJuros = formatDecimalValue(installment.valor_juros) || formatDecimalValue(0)
  installmentEditModal.valorTotal = formatDecimalValue(installment.valor_total) || formatDecimalValue(0)
}

function openInstallmentCreateModal() {
  if (!currentContractId.value) {
    return
  }

  if (form.quitado) {
    void infoAlert('Este contrato nao permite incluir parcelas porque esta quitado.')
    return
  }

  const suggestedBaseValue = props.initialContract?.valor_parcela ?? persistedInstallments.value.at(-1)?.valor_base ?? 0
  const suggestedInterestValue = persistedInstallments.value.at(-1)?.valor_juros ?? 0

  installmentEditModal.open = true
  installmentEditModal.mode = 'create'
  installmentEditModal.installmentId = null
  installmentEditModal.parcelaNro = String(getNextInstallmentNumber())
  installmentEditModal.vencimento = currentDateInputValue()
  installmentEditModal.valorBase = formatDecimalValue(suggestedBaseValue) || formatDecimalValue(0)
  installmentEditModal.valorJuros = formatDecimalValue(suggestedInterestValue) || formatDecimalValue(0)
  installmentEditModal.valorTotal = formatDecimalValue((suggestedBaseValue ?? 0) + (suggestedInterestValue ?? 0)) || formatDecimalValue(0)
}

function closeInstallmentEditModal() {
  installmentEditModal.open = false
  installmentEditModal.mode = 'edit'
  installmentEditModal.installmentId = null
  installmentEditModal.parcelaNro = ''
  installmentEditModal.vencimento = ''
  installmentEditModal.valorBase = ''
  installmentEditModal.valorJuros = ''
  installmentEditModal.valorTotal = ''
}

function syncInstallmentEditTotal() {
  const baseValue = toLocaleNumberOrNull(installmentEditModal.valorBase) ?? 0
  const interestValue = toLocaleNumberOrNull(installmentEditModal.valorJuros) ?? 0
  installmentEditModal.valorTotal = formatDecimalValue(baseValue + interestValue) || formatDecimalValue(0)
}

function formatInstallmentEditField(field: 'valorBase') {
  const parsed = toLocaleNumberOrNull(installmentEditModal[field])
  installmentEditModal[field] = parsed === null ? '' : formatDecimalValue(parsed)
  syncInstallmentEditTotal()
}

async function saveInstallmentEdit() {
  if (installmentEditModal.mode === 'edit' && !installmentEditModal.installmentId) {
    return
  }

  if (installmentEditModal.mode === 'create' && !currentContractId.value) {
    return
  }

  const parcelaNro = toIntegerOrNull(installmentEditModal.parcelaNro)
  const valorBase = toLocaleNumberOrNull(installmentEditModal.valorBase)
  const valorJuros = toLocaleNumberOrNull(installmentEditModal.valorJuros) ?? 0

  if (parcelaNro === null || parcelaNro <= 0 || !installmentEditModal.vencimento || valorBase === null) {
    await infoAlert('Preencha numero da parcela, vencimento e valor antes de salvar.')
    return
  }

  installmentsSaving.value = true
  try {
    const modalMode = installmentEditModal.mode
    const payload: InstallmentCreatePayload | InstallmentUpdatePayload = {
      parcela_nro: parcelaNro,
      vencimento: toApiDueDateTime(installmentEditModal.vencimento),
      valor_base: valorBase,
      valor_juros: valorJuros,
      valor_total: valorBase + valorJuros,
    }

    const updated = modalMode === 'create'
      ? await createContractInstallment(currentContractId.value as number, payload as InstallmentCreatePayload)
      : await updateContractInstallment(installmentEditModal.installmentId as number, payload as InstallmentUpdatePayload)

    updateInstallmentInState(updated)
    syncQuitadoFromInstallments()
    syncFinancialTotalsFromInstallments()
    closeInstallmentEditModal()
    void successAlert(modalMode === 'create' ? 'Parcela incluída com sucesso.' : 'Parcela alterada com sucesso.', 'update')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : installmentEditModal.mode === 'create' ? 'Falha ao incluir parcela' : 'Falha ao alterar parcela')
  } finally {
    installmentsSaving.value = false
  }
}

async function handleDeleteInstallmentPayment(installmentId: number | null) {
  if (!installmentId) {
    return
  }

  installmentsSaving.value = true
  try {
    const receipts = await listInstallmentReceipts(installmentId)
    if (receipts.length === 0) {
      await infoAlert('Nao existem pagamentos lancados para esta parcela.')
      return
    }

    const receiptIds = await chooseReceiptToDeletePrompt(
      receipts.map((receipt) => ({
        id: receipt.recebimento_id,
        title: `${formatCurrency(receipt.valor_recebido)} em ${formatDateLabel(receipt.data_recebimento)}`,
        description: `Recebido por ${receipt.usuario_nome || 'Usuario nao identificado'}${receipt.juros ? ` | Juros ${formatCurrency(receipt.juros)}` : ''}${receipt.desconto ? ` | Desconto ${formatCurrency(receipt.desconto)}` : ''}`,
      })),
    )

    if (!receiptIds || receiptIds.length === 0) {
      return
    }

    let updated: ContractInstallment | null = null
    for (const receiptId of receiptIds) {
      updated = await deleteReceiptPayment(receiptId)
    }

    if (!updated) {
      return
    }

    updateInstallmentInState(updated)
    syncQuitadoFromInstallments()
    syncFinancialTotalsFromInstallments()
    void successAlert('Pagamento excluído com sucesso.', 'delete')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao excluir pagamento da parcela')
  } finally {
    installmentsSaving.value = false
  }
}

function updateInstallmentInState(updated: ContractInstallment) {
  const index = persistedInstallments.value.findIndex((item) => item.id === updated.id)
  if (index === -1) {
    persistedInstallments.value = [...persistedInstallments.value, updated]
    syncContractDueDateFromInstallments()
    return
  }

  persistedInstallments.value = persistedInstallments.value.map((item) => (item.id === updated.id ? updated : item))
  syncContractDueDateFromInstallments()
}

function syncQuitadoFromInstallments() {
  form.quitado = persistedInstallments.value.length > 0 && persistedInstallments.value.every((item) => Boolean(item.quitado))
}

function syncFinancialTotalsFromInstallments() {
  syncContractFinalValueFromInstallments()
  syncContractDueDateFromInstallments()
  applyFinancialTotals(
    summarizeInstallmentTotals(
      persistedInstallments.value.map((item) => ({
        dueDate: item.vencimentol ?? item.vencimento_original,
        totalValue: item.valor_total,
        receivedValue: item.valor_recebido,
        quitado: item.quitado,
      })),
    ),
  )
}

function syncFinancialTotalsFromPreview(dueDates: Date[], installmentValue: number) {
  form.valor_final = formatDecimalValue(dueDates.length * installmentValue)
  applyFinancialTotals(
    summarizeInstallmentTotals(
      dueDates.map((dueDate) => ({
        dueDate: dueDate.toISOString(),
        totalValue: installmentValue,
        receivedValue: 0,
        quitado: false,
      })),
    ),
  )
}

function syncContractFinalValueFromInstallments() {
  if (persistedInstallments.value.length === 0) {
    return
  }

  const totalValue = persistedInstallments.value.reduce((sum, item) => sum + (item.valor_total ?? 0), 0)
  form.valor_final = formatDecimalValue(totalValue)
}

function syncContractDueDateFromInstallments() {
  if (persistedInstallments.value.length === 0) {
    return
  }

  const latestInstallment = [...persistedInstallments.value].sort(compareInstallments).at(-1)
  form.data_final = latestInstallment ? toDateTimeLocal(latestInstallment.vencimentol ?? latestInstallment.vencimento_original) : ''
}

function summarizeInstallmentTotals(
  installments: Array<{ dueDate: string | null; totalValue: number | null; receivedValue: number | null; quitado: boolean | null }>,
) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  let totalReceived = 0
  let totalOpen = 0
  let totalOverdue = 0

  for (const installment of installments) {
    const totalValue = installment.totalValue ?? 0
    const receivedValue = installment.receivedValue ?? 0
    const remainingValue = installment.quitado ? 0 : Math.max(totalValue - receivedValue, 0)

    totalReceived += receivedValue
    totalOpen += remainingValue

    if (remainingValue > 0 && installment.dueDate) {
      const dueDate = toCalendarDate(installment.dueDate)
      if (!dueDate) {
        continue
      }

      if (dueDate < today) {
        totalOverdue += remainingValue
      }
    }
  }

  return {
    valorRecebido: totalReceived,
    valorEmAberto: totalOpen,
    valorEmAtraso: totalOverdue,
  }
}

function applyFinancialTotals(totals: { valorRecebido: number; valorEmAberto: number; valorEmAtraso: number }) {
  form.valor_recebido = formatDecimalValue(totals.valorRecebido) || formatDecimalValue(0)
  form.valor_em_aberto = formatDecimalValue(totals.valorEmAberto) || formatDecimalValue(0)
  form.valor_em_atraso = formatDecimalValue(totals.valorEmAtraso) || formatDecimalValue(0)
}

function resetFinancialTotals() {
  applyFinancialTotals({
    valorRecebido: 0,
    valorEmAberto: 0,
    valorEmAtraso: 0,
  })
}

function submitForm() {
  if (props.mode === 'create') {
    emit('submit', {
      contract: buildCreatePayload(),
      installments: previewInstallmentsPayload.value,
    })
    return
  }

  emit('submit', {
    contract: buildUpdatePayload(),
    installments: null,
  })
}

function buildCreatePayload(): ContractCreateInput {
  return {
    contratos_id: Number(form.contratos_id),
    ...buildCommonPayload(),
  }
}

function buildUpdatePayload(): ContractUpdateInput {
  return buildCommonPayload()
}

function buildCommonPayload(): ContractUpdateInput {
  return {
    data_lancto: form.data_lancto || null,
    data_contrato: form.data_contrato || null,
    cliente_id: form.cliente_id,
    plano_id: form.plano_id,
    qtde_dias: toIntegerOrNull(form.qtde_dias),
    percent_juros: toLocaleNumberOrNull(form.percent_juros),
    valor_empretismo: toLocaleNumberOrNull(form.valor_empretismo),
    data_final: form.data_final || null,
    valor_final: toLocaleNumberOrNull(form.valor_final),
    quitado: form.quitado,
    obs: form.obs.trim() || null,
    valor_parcela: toLocaleNumberOrNull(form.valor_parcela),
    user_add: form.user_add,
    contrato_status: Number(form.contrato_status || '1'),
    negociacao_id: toNumberOrNull(form.negociacao_id),
    usuario_id_vendedor: form.usuario_id_vendedor,
    comissao_percentual: toNumberOrNull(form.comissao_percentual),
    valor_comissao_previsto: toNumberOrNull(form.valor_comissao_previsto),
    valor_comissao_apurada: toNumberOrNull(form.valor_comissao_apurada),
    regra_comissao_id: form.regra_comissao_id,
    regra_juros_id: toNumberOrNull(form.regra_juros_id),
    aluguel: form.aluguel,
    recorrencia: form.recorrencia,
    cobranca_segunda: billingDays.segunda,
    cobranca_terca: billingDays.terca,
    cobranca_quarta: billingDays.quarta,
    cobranca_quinta: billingDays.quinta,
    cobranca_sexta: billingDays.sexta,
    cobranca_sabado: billingDays.sabado,
    cobranca_domingo: billingDays.domingo,
    cobranca_feriado: billingDays.feriado,
    cobranca_mensal: billingDays.mensal,
    cobranca_quinzenal: billingDays.quinzenal,
  }
}

function handleNew() {
  if (props.mode === 'create') {
    resetForm()
    return
  }

  emit('new')
}

function openClientModal() {
  if (contractEditLocked.value) {
    void infoAlert('Este contrato nao permite trocar o cliente porque ja possui recebimentos ou parcelas quitadas.')
    return
  }

  clientModal.open = true
  clientModal.term = ''
}

function closeClientModal() {
  clientModal.open = false
  clientModal.term = ''
}

function selectClient(clientId: number) {
  form.cliente_id = clientId
  closeClientModal()
}

async function handleOpenClientScoreLog(client: Client) {
  if (!client.clientes_id) {
    return
  }

  const logs = await listClientScoreLogs(client.clientes_id)
  await showClientScoreLogPopup(client.nome || 'Cliente', logs.items)
}

async function hydrateClientCities() {
  const ufList = [...new Set(clientOptions.value.map((client) => client.uf).filter((uf): uf is string => Boolean(uf)))]

  await Promise.all(
    ufList.map(async (uf) => {
      const cities = await listCitiesByUf(uf)
      registerCities(cities)
    }),
  )
}

function registerCities(cities: CidadeOption[]) {
  for (const city of cities) {
    cityLabels[city.cidade_id] = city.cidade
  }
}

async function assignNextContractNumber() {
  try {
    const { listContracts } = await import('@/services/contractService')
    const response = await listContracts({ page: 1, page_size: 1 })
    const nextId = response.items[0]?.contratos_id ? response.items[0].contratos_id + 1 : 1
    form.contratos_id = String(nextId)
  } catch {
    form.contratos_id = '1'
  }
}

function currentDateTimeLocal() {
  return toApiDateTimeLocal(new Date()).slice(0, 16)
}

function currentDateInputValue() {
  const date = new Date()
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getNextInstallmentNumber() {
  const highestInstallmentNumber = persistedInstallments.value.reduce((highest, item) => Math.max(highest, item.parcela_nro ?? 0), 0)
  return highestInstallmentNumber + 1
}

function toApiDateTimeLocal(date: Date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`
}

function calculateMonthlyInterestRate(startDate: Date, endDate: Date, principalValue: number, finalValue: number) {
  const totalInterest = finalValue - principalValue
  if (totalInterest <= 0) {
    return 0
  }

  const monthSpan = calculateMonthSpan(startDate, endDate)
  return (totalInterest / principalValue / monthSpan) * 100
}

function calculateMonthSpan(startDate: Date, endDate: Date) {
  const millisecondsPerDay = 24 * 60 * 60 * 1000
  const diffInMilliseconds = endDate.getTime() - startDate.getTime()
  const diffInDays = diffInMilliseconds / millisecondsPerDay

  if (diffInDays <= 0) {
    return 1
  }

  return Math.max(diffInDays / 30, 1)
}

function toDateTimeLocal(value: string | null) {
  if (!value) {
    return ''
  }

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }

  const timezoneOffset = date.getTimezoneOffset() * 60000
  return new Date(date.getTime() - timezoneOffset).toISOString().slice(0, 16)
}

function toDateInputValue(value: string | null) {
  const calendarDate = value ? parseCalendarDate(value) : null
  if (!calendarDate) {
    return ''
  }

  return `${calendarDate.year}-${String(calendarDate.month).padStart(2, '0')}-${String(calendarDate.day).padStart(2, '0')}`
}

function toApiDueDateTime(value: string) {
  return `${value}T12:00:00`
}

function parseLocalDateTime(value: string) {
  if (!value) {
    return null
  }

  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/)
  if (!match) {
    return null
  }

  const parsed = new Date(
    Number(match[1]),
    Number(match[2]) - 1,
    Number(match[3]),
    Number(match[4]),
    Number(match[5]),
  )
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

function resetBillingDays() {
  billingDays.sabado = defaultBillingDays.sabado
  billingDays.domingo = defaultBillingDays.domingo
  billingDays.feriado = defaultBillingDays.feriado
  billingDays.mensal = defaultBillingDays.mensal
  billingDays.quinzenal = defaultBillingDays.quinzenal
  billingDays.segunda = defaultBillingDays.segunda
  billingDays.terca = defaultBillingDays.terca
  billingDays.quarta = defaultBillingDays.quarta
  billingDays.quinta = defaultBillingDays.quinta
  billingDays.sexta = defaultBillingDays.sexta
}

function hasSelectedBillingDays() {
  return Object.values(billingDays).some(Boolean)
}

function toStringValue(value: number | null | undefined) {
  return typeof value === 'number' ? String(value) : ''
}

function formatDecimalValue(value: number | null | undefined) {
  if (typeof value !== 'number') {
    return ''
  }

  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

function formatIntegerValue(value: number | null | undefined) {
  if (typeof value !== 'number') {
    return ''
  }

  return String(Math.trunc(value))
}

function toLocaleNumberOrNull(value: string) {
  const trimmed = value.trim()
  if (!trimmed) {
    return null
  }

  const normalized = trimmed.replace(/\./g, '').replace(',', '.')
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : null
}

function toIntegerOrNull(value: string) {
  const parsed = toLocaleNumberOrNull(value)
  if (parsed === null) {
    return null
  }

  return Math.trunc(parsed)
}

function toNumberOrNull(value: string) {
  const trimmed = value.trim()
  if (!trimmed) {
    return null
  }

  const parsed = Number(trimmed)
  return Number.isFinite(parsed) ? parsed : null
}

function formatDecimalField(field: 'valor_empretismo' | 'percent_juros' | 'valor_final' | 'valor_parcela') {
  const parsed = toLocaleNumberOrNull(form[field])
  form[field] = parsed === null ? '' : formatDecimalValue(parsed)
}

function buildDueDates(startDate: Date, qtdDias: number, holidaySet: Set<string>) {
  if (billingDays.mensal) {
    return buildMonthlyDueDates(startDate, qtdDias, holidaySet)
  }

  if (billingDays.quinzenal) {
    return buildBiweeklyDueDates(startDate, qtdDias, holidaySet)
  }

  return buildWeeklyDueDates(startDate, qtdDias, holidaySet)
}

function buildSingleScheduledDueDate(startDate: Date, holidaySet: Set<string>) {
  if (billingDays.mensal) {
    const candidate = addMonths(startDate, 1)
    return [resolveMonthlyDueDate(candidate, holidaySet)]
  }

  if (billingDays.quinzenal) {
    const candidate = new Date(startDate)
    candidate.setDate(candidate.getDate() + 15)
    return [resolveMonthlyDueDate(candidate, holidaySet)]
  }

  return buildWeeklyDueDates(startDate, 1, holidaySet)
}

function buildMonthlyDueDates(startDate: Date, qtdDias: number, holidaySet: Set<string>) {
  const dates: Date[] = []
  const cursor = new Date(startDate)
  let generated = 0

  while (generated < qtdDias) {
    const candidate = resolveMonthlyDueDate(cursor, holidaySet)
    dates.push(candidate)
    generated += 1
    cursor.setMonth(cursor.getMonth() + 1)
  }

  return dates
}

function resolveMonthlyDueDate(baseDate: Date, holidaySet: Set<string>) {
  const candidate = new Date(baseDate)
  let safety = 0

  while (!shouldAllowMonthlyDueDate(candidate, holidaySet)) {
    candidate.setDate(candidate.getDate() + 1)
    safety += 1

    if (safety > 370) {
      break
    }
  }

  return candidate
}

function shouldAllowMonthlyDueDate(date: Date, holidaySet: Set<string>) {
  const weekday = date.getDay()

  if (!billingDays.domingo && weekday === 0) {
    return false
  }

  if (!billingDays.sabado && weekday === 6) {
    return false
  }

  if (!billingDays.feriado && holidaySet.has(formatDateKey(date))) {
    return false
  }

  return true
}

function buildBiweeklyDueDates(startDate: Date, qtdDias: number, holidaySet: Set<string>) {
  const dates: Date[] = []
  const cursor = new Date(startDate)
  let generated = 0

  while (generated < qtdDias) {
    const candidate = resolveMonthlyDueDate(cursor, holidaySet)
    dates.push(candidate)
    generated += 1
    cursor.setDate(cursor.getDate() + 15)
  }

  return dates
}

function buildWeeklyDueDates(startDate: Date, qtdDias: number, holidaySet: Set<string>) {
  const allowedWeekdays = getAllowedWeekdays()

  const dates: Date[] = []
  const cursor = new Date(startDate)
  let generated = 0

  while (generated < qtdDias) {
    if (allowedWeekdays.has(cursor.getDay()) && shouldIncludeDate(cursor, holidaySet)) {
      dates.push(new Date(cursor))
      generated += 1
    }
    cursor.setDate(cursor.getDate() + 1)
  }

  return dates
}

function shouldIncludeDate(date: Date, holidaySet: Set<string>) {
  if (!billingDays.feriado && holidaySet.has(formatDateKey(date))) {
    return false
  }

  return true
}

function hasAnyWeeklyBillingDaySelected() {
  return billingDays.domingo || billingDays.segunda || billingDays.terca || billingDays.quarta || billingDays.quinta || billingDays.sexta || billingDays.sabado
}

function getAllowedWeekdays() {
  const allowedWeekdays = new Set<number>()
  if (billingDays.domingo) allowedWeekdays.add(0)
  if (billingDays.segunda) allowedWeekdays.add(1)
  if (billingDays.terca) allowedWeekdays.add(2)
  if (billingDays.quarta) allowedWeekdays.add(3)
  if (billingDays.quinta) allowedWeekdays.add(4)
  if (billingDays.sexta) allowedWeekdays.add(5)
  if (billingDays.sabado) allowedWeekdays.add(6)
  return allowedWeekdays
}

function addMonths(value: Date, months: number) {
  const next = new Date(value)
  next.setMonth(next.getMonth() + months)
  return next
}

async function loadHolidaySet() {
  if (billingDays.feriado) {
    return new Set<string>()
  }

  const client = clientOptions.value.find((item) => item.clientes_id === form.cliente_id)
  const nationalCacheKey = '__nacionais__'

  if (!holidayCache[nationalCacheKey]) {
    holidayCache[nationalCacheKey] = await listFeriados({ nivel: 1 })
  }

  if (!client) {
    return new Set(holidayCache[nationalCacheKey].map((item) => formatDateKey(item.data)))
  }

  const cacheKey = `${client.uf ?? ''}:${client.cidade_id ?? ''}`
  if (!holidayCache[cacheKey]) {
    const [estaduais, municipais] = await Promise.all([
      client.uf ? listFeriados({ nivel: 2, uf: client.uf }) : Promise.resolve([]),
      typeof client.cidade_id === 'number' ? listFeriados({ nivel: 3, cidade_id: client.cidade_id }) : Promise.resolve([]),
    ])
    holidayCache[cacheKey] = [...holidayCache[nationalCacheKey], ...estaduais, ...municipais]
  }

  return new Set(holidayCache[cacheKey].map((item) => formatDateKey(item.data)))
}

function formatDateKey(value: Date | string) {
  if (typeof value === 'string') {
    const isoMatch = value.match(/^(\d{4})-(\d{2})-(\d{2})/)
    if (isoMatch) {
      return `${isoMatch[1]}-${isoMatch[2]}-${isoMatch[3]}`
    }
  }

  const date = typeof value === 'string' ? new Date(value) : value
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function compareInstallments(left: ContractInstallment, right: ContractInstallment) {
  const dueDateDiff = getInstallmentSortTime(left) - getInstallmentSortTime(right)
  if (dueDateDiff !== 0) {
    return dueDateDiff
  }

  const parcelaDiff = (left.parcela_nro ?? Number.MAX_SAFE_INTEGER) - (right.parcela_nro ?? Number.MAX_SAFE_INTEGER)
  if (parcelaDiff !== 0) {
    return parcelaDiff
  }

  return left.id - right.id
}

function getInstallmentSortTime(installment: ContractInstallment) {
  const calendarDate = parseCalendarDate(installment.vencimentol ?? installment.vencimento_original ?? '')
  if (!calendarDate) {
    return Number.MAX_SAFE_INTEGER
  }

  return new Date(calendarDate.year, calendarDate.month - 1, calendarDate.day).getTime()
}

function formatDateLabel(value: string | null) {
  if (!value) {
    return '-'
  }

  const calendarDate = parseDisplayCalendarDate(value)
  if (!calendarDate) {
    return '-'
  }

  return `${String(calendarDate.day).padStart(2, '0')}/${String(calendarDate.month).padStart(2, '0')}/${calendarDate.year}`
}

function formatWeekdayLabel(value: string | null) {
  if (!value) {
    return '-'
  }

  const calendarDate = parseDisplayCalendarDate(value)
  if (!calendarDate) {
    return '-'
  }

  return new Intl.DateTimeFormat('pt-BR', { weekday: 'long' })
    .format(new Date(calendarDate.year, calendarDate.month - 1, calendarDate.day))
    .toUpperCase()
}

function parseCalendarDate(value: string) {
  const isoMatch = value.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (!isoMatch) {
    return null
  }

  return {
    year: Number(isoMatch[1]),
    month: Number(isoMatch[2]),
    day: Number(isoMatch[3]),
  }
}

function parseDisplayCalendarDate(value: string) {
  const parsedDate = new Date(value)
  if (!Number.isNaN(parsedDate.getTime()) && value.includes('T')) {
    return {
      year: parsedDate.getFullYear(),
      month: parsedDate.getMonth() + 1,
      day: parsedDate.getDate(),
    }
  }

  return parseCalendarDate(value)
}

function isInstallmentOverdue(
  dueDateValue: string | Date | null,
  quitado: boolean | null | undefined,
  totalValue: number | null | undefined,
  receivedValue: number | null | undefined,
) {
  return calculateInstallmentOverdueDays(dueDateValue, quitado, totalValue, receivedValue) > 0
}

function calculateInstallmentOverdueDays(
  dueDateValue: string | Date | null,
  quitado: boolean | null | undefined,
  totalValue: number | null | undefined,
  receivedValue: number | null | undefined,
) {
  if (quitado) {
    return 0
  }

  const dueDate = toCalendarDate(dueDateValue)
  if (!dueDate) {
    return 0
  }

  const remainingValue = Math.max((totalValue ?? 0) - (receivedValue ?? 0), 0)
  if (remainingValue <= 0) {
    return 0
  }

  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const diffMs = today.getTime() - dueDate.getTime()
  if (diffMs <= 0) {
    return 0
  }

  return Math.floor(diffMs / 86_400_000)
}

function formatInstallmentOverdueDays(
  dueDateValue: string | Date | null,
  quitado: boolean | null | undefined,
  totalValue: number | null | undefined,
  receivedValue: number | null | undefined,
) {
  const overdueDays = calculateInstallmentOverdueDays(dueDateValue, quitado, totalValue, receivedValue)
  return overdueDays > 0 ? String(overdueDays) : ''
}

function toCalendarDate(value: string | Date | null) {
  if (!value) {
    return null
  }

  if (value instanceof Date) {
    const calendarDate = parseCalendarDate(value.toISOString())
    return calendarDate ? new Date(calendarDate.year, calendarDate.month - 1, calendarDate.day) : null
  }

  const calendarDate = parseCalendarDate(value)
  if (!calendarDate) {
    return null
  }

  return new Date(calendarDate.year, calendarDate.month - 1, calendarDate.day)
}

function formatCurrency(value: number | null) {
  if (typeof value !== 'number') {
    return '-'
  }

  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value)
}

async function handleSendInstallmentWhatsApp(installmentId: number | null) {
  if (!installmentId) {
    return
  }

  const installment = persistedInstallments.value.find((item) => item.id === installmentId)
  const selectedClient = clientOptions.value.find((item) => item.clientes_id === form.cliente_id)
  if (selectedClient?.nao_enviar_whatsapp) {
    await infoAlert('Este cliente está marcado para não enviar WhatsApp.')
    return
  }
  if (!selectedClient?.flag_whatsapp || !selectedClient.celular01?.trim()) {
    await infoAlert('Cliente sem WhatsApp ativo no celular principal.')
    return
  }

  if (installment?.msg_whatsapp) {
    const confirmed = await confirmActionAlert(
      'Mensagem já enviada',
      'Esta parcela já foi enviada no WhatsApp. Deseja reenviar?',
      'Reenviar',
    )
    if (!confirmed) {
      return
    }
  }

  installmentsSaving.value = true
  try {
    const response = await sendInstallmentWhatsAppMessage(installmentId)
    if (currentContractId.value) {
      await loadInstallments(currentContractId.value)
    }
    await successAlert(response.message || 'Mensagem enviada com sucesso.', 'update')
  } catch (error) {
    await errorAlert(error instanceof Error ? error.message : 'Falha ao enviar mensagem da parcela via WhatsApp')
  } finally {
    installmentsSaving.value = false
  }
}

function formatScore(value: number | null) {
  if (typeof value !== 'number') {
    return '-'
  }

  return new Intl.NumberFormat('pt-BR', {
    maximumFractionDigits: 0,
  }).format(value)
}

function clientScoreClass(value: number | null) {
  if (typeof value !== 'number') {
    return 'contract-client-result--neutral'
  }
  if (value < 500) {
    return 'contract-client-result--danger'
  }
  if (value > 500) {
    return 'contract-client-result--success'
  }
  return 'contract-client-result--neutral'
}

function formatDocument(value: string | null | undefined) {
  const digits = (value ?? '').replace(/\D/g, '')
  if (!digits) {
    return '-'
  }
  if (digits.length <= 11) {
    return digits
      .slice(0, 11)
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d{1,2})$/, '$1-$2')
  }

  return digits
    .slice(0, 14)
    .replace(/(\d{2})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1/$2')
    .replace(/(\d{4})(\d{1,2})$/, '$1-$2')
}

function formatClientAddress(client: Client) {
  const city = client.cidade_id ? cityLabels[client.cidade_id] ?? `Cidade ${client.cidade_id}` : 'Cidade não informada'
  const number = client.nro?.trim() ? `, ${client.nro.trim()}` : ''
  const uf = client.uf ? `-${client.uf}` : ''
  const address = client.endereco?.trim() || 'Endereço não informado'
  return `${address}${number} ${city}${uf}`.trim()
}
</script>

<style scoped>
.contract-client-result--danger {
  background: rgba(220, 38, 38, 0.1);
  border-color: rgba(220, 38, 38, 0.28);
}

.contract-client-result--success {
  background: rgba(22, 163, 74, 0.1);
  border-color: rgba(22, 163, 74, 0.28);
}

.contract-client-result--neutral {
  background: rgba(255, 255, 255, 0.96);
}

.contract-client-result__score-link {
  cursor: pointer;
  text-decoration: underline;
  text-decoration-color: rgba(15, 118, 110, 0.45);
  text-underline-offset: 2px;
}

.icon-action--message {
  background: rgba(22, 163, 74, 0.14);
  border: 1px solid rgba(22, 163, 74, 0.28);
  color: #15803d;
}

.icon-action--sent {
  background: rgba(220, 38, 38, 0.16);
  border: 1px solid rgba(220, 38, 38, 0.34);
  box-shadow: inset 0 0 0 1px rgba(220, 38, 38, 0.08);
  color: #b91c1c;
}
</style>