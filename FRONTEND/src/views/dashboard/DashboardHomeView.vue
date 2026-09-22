<template>
  <section class="dashboard">
    <div class="dashboard__content">
      <aside class="dashboard__sidebar">
        <form class="contract-search surface" @submit.prevent="openContract">
          <div class="icon-box icon-box--orange">#</div>
          <div class="contract-search__copy"><p class="eyebrow">Acesso rápido</p><h2>Localizar contrato</h2></div>
          <button class="contract-search__create" type="button" title="Criar novo contrato" aria-label="Criar novo contrato" @click="goTo('contracts-create')">+</button>
          <div class="contract-search__input"><input ref="contractInput" v-model="contractNumber" inputmode="numeric" placeholder="Digite o número" aria-label="Número do contrato"><button type="submit" aria-label="Abrir contrato">→</button></div>
        </form>

        <nav class="shortcuts" aria-label="Atalhos">
          <button type="button" @click="goTo('clients-list')"><span class="shortcut-icon shortcut-icon--rose">♙</span><span>Clientes</span><i>→</i></button>
          <button type="button" @click="goTo('contracts-list')"><span class="shortcut-icon shortcut-icon--orange">▤</span><span>Contratos</span><i>→</i></button>
          <button type="button" @click="goTo('batch-receipt')"><span class="shortcut-icon shortcut-icon--blue">↓</span><span>Baixa em lote</span><i>→</i></button>
        </nav>

        <article class="renewals surface">
          <header class="renewals__header"><div><p class="eyebrow">Renovações</p><h2>Contratos finalizando</h2></div><strong>{{ summary.total_contratos_finalizando }}</strong></header>
          <div class="renewals__filter"><span>Próximos <b>{{ endingDays }} dias</b></span><input v-model.number="endingDays" type="range" min="1" max="10" aria-label="Dias para finalização"><output>{{ endingDays }}</output></div>
          <div class="renewals__list">
            <p v-if="loading" class="empty">Atualizando dados…</p>
            <button v-for="item in summary.contratos_finalizando" :key="item.contratos_id" type="button" class="renewal-item" @click="goTo('contracts-edit', { id: item.contratos_id })"><b>#{{ item.contratos_id }}</b><span>{{ item.cliente_nome || 'Cliente não informado' }}</span><small :class="{ today: item.dias_para_finalizar === 0 }">{{ item.dias_para_finalizar === 0 ? 'Hoje' : `${item.dias_para_finalizar} dias` }}</small></button>
            <p v-if="!loading && !summary.contratos_finalizando.length" class="empty">Nenhum contrato neste período.</p>
          </div>
          <button v-if="summary.total_contratos_finalizando" type="button" class="text-button" @click="goTo('contracts-list')">Ver todos <span>→</span></button>
        </article>
      </aside>

      <main class="dashboard__main">
        <article class="chart-panel surface">
          <header class="chart-panel__header"><div><p class="eyebrow">Financeiro</p><h2>Recebidos e previsão</h2><p class="subtitle">{{ chartTitle }}</p></div><div class="chart-controls"><select v-model="grouping" aria-label="Agrupamento do gráfico"><option value="dia">Por dia</option><option value="ano">Por ano</option></select><input v-model="reference" :type="grouping === 'dia' ? 'month' : 'number'" aria-label="Período do gráfico"></div></header>
          <section class="kpis" aria-label="Totais do período"><div><span class="kpis__marker kpis__marker--green"></span><p>Recebido</p><strong>{{ currency(totalReceived) }}</strong></div><div><span class="kpis__marker kpis__marker--amber"></span><p>Previsão</p><strong>{{ currency(totalForecast) }}</strong></div><div class="kpis__difference"><p>Realização</p><strong>{{ achievement }}%</strong></div></section>
          <div class="chart" :class="{ 'chart--year': grouping === 'ano' }"><div v-for="point in visiblePoints" :key="point.label" class="chart__column" :title="`${point.label}: recebido ${currency(point.recebido)} | previsto ${currency(point.previsto)}`"><div class="chart__bars"><i class="bar bar--forecast" :style="{ height: barHeight(point.previsto) }"></i><i class="bar bar--received" :style="{ height: barHeight(point.recebido) }"></i></div><small>{{ point.label }}</small></div></div>
          <footer class="chart-legend"><span><i class="legend legend--received"></i>Recebido</span><span><i class="legend legend--forecast"></i>Previsão de recebimento</span></footer>
        </article>
      </main>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getContractById } from '@/services/contractService'
import { getDashboardSummary, type DashboardGrouping, type DashboardSummary } from '@/services/dashboardService'
import { warningToast } from '@/services/alertService'

const router = useRouter()
const now = new Date()
const grouping = ref<DashboardGrouping>('dia')
const reference = ref(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`)
const endingDays = ref(7)
const contractNumber = ref('')
const contractInput = ref<HTMLInputElement | null>(null)
const loading = ref(false)
const summary = ref<DashboardSummary>({ pontos: [], contratos_finalizando: [], total_contratos_finalizando: 0 })

const chartTitle = computed(() => grouping.value === 'ano' ? `Ano de ${reference.value}` : new Intl.DateTimeFormat('pt-BR', { month: 'long', year: 'numeric' }).format(new Date(`${reference.value}-02T12:00:00`)))
const totalReceived = computed(() => summary.value.pontos.reduce((sum, item) => sum + item.recebido, 0))
const totalForecast = computed(() => summary.value.pontos.reduce((sum, item) => sum + item.previsto, 0))
const achievement = computed(() => totalForecast.value ? Math.round((totalReceived.value / totalForecast.value) * 100) : 0)
const maximum = computed(() => Math.max(1, ...summary.value.pontos.flatMap(item => [item.recebido, item.previsto])))
const visiblePoints = computed(() => grouping.value === 'dia' ? summary.value.pontos.filter((_, index) => index % 2 === 0 || summary.value.pontos.length <= 16) : summary.value.pontos)

function currency(value: number) { return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value || 0) }
function barHeight(value: number) { return `${Math.max(value ? 4 : 0, (value / maximum.value) * 100)}%` }
async function loadDashboard() { loading.value = true; try { summary.value = await getDashboardSummary(grouping.value, grouping.value === 'ano' ? `${reference.value}-01-01` : `${reference.value}-01`, endingDays.value) } finally { loading.value = false } }
function goTo(name: string, params?: Record<string, number>) { router.push({ name, params }) }
async function openContract() {
  const id = Number(contractNumber.value)
  if (Number.isInteger(id) && id > 0) {
    try {
      await getContractById(id)
      goTo('contracts-edit', { id })
      return
    } catch {
      // A mensagem abaixo orienta a nova tentativa sem abrir uma tela inexistente.
    }
  }

  contractNumber.value = ''
  void warningToast('Contrato não encontrado. Confira o número e tente novamente.')
  await nextTick()
  contractInput.value?.focus()
}

watch([grouping, reference, endingDays], loadDashboard)
onMounted(loadDashboard)
</script>

<style scoped>
.dashboard{max-width:1420px;margin:0 auto;padding-bottom:16px}.dashboard h1,.dashboard h2,.dashboard p{margin:0}.dashboard__header{display:flex;align-items:center;justify-content:space-between;gap:20px;margin:4px 0 28px}.dashboard h1{margin-top:3px;font-size:31px;letter-spacing:-.055em;color:#1f2b37}.dashboard h2{font-size:18px;letter-spacing:-.035em;color:#273543}.eyebrow{font-size:10px;font-weight:850;letter-spacing:.13em;text-transform:uppercase;color:#ce650f}.subtitle{margin-top:6px!important;color:var(--text-muted);font-size:13px}.button-primary{display:inline-flex;align-items:center;gap:7px;padding:12px 17px;border:0;border-radius:11px;background:linear-gradient(135deg,#f88022,#df5b09);color:#fff;box-shadow:0 10px 20px rgba(225,102,16,.2);font-weight:800;cursor:pointer;transition:transform .16s,box-shadow .16s}.button-primary span{font-size:19px;line-height:12px}.button-primary:hover{transform:translateY(-1px);box-shadow:0 13px 23px rgba(225,102,16,.27)}.dashboard__content{display:grid;grid-template-columns:340px minmax(0,1fr);gap:24px}.dashboard__sidebar{display:grid;align-content:start;gap:14px}.surface{background:rgba(255,255,255,.93);border:1px solid rgba(36,48,59,.075);border-radius:18px;box-shadow:0 14px 35px rgba(48,63,77,.07)}.contract-search{display:grid;grid-template-columns:auto 1fr;gap:12px;padding:17px}.icon-box{display:grid;place-items:center;width:39px;height:39px;border-radius:12px;font-weight:900}.icon-box--orange{color:#cf650e;background:#fff0e1}.contract-search__copy{align-self:center}.contract-search__input{grid-column:1/-1;display:flex;gap:8px;margin-top:3px}.contract-search input{width:100%;min-width:0;padding:11px 12px;border:1px solid #e7e9ec;border-radius:10px;background:#fbfcfd;outline-color:var(--accent);font-size:13px}.contract-search button{width:42px;border:0;border-radius:10px;background:#263c51;color:white;font-size:20px;cursor:pointer}.shortcuts{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}.shortcuts button{display:grid;grid-template-rows:auto 1fr auto;justify-items:start;min-height:112px;padding:13px 12px;border:1px solid rgba(36,48,59,.06);border-radius:15px;background:#fff;color:#344151;text-align:left;font-size:11px;font-weight:800;box-shadow:0 8px 20px rgba(48,63,77,.04);cursor:pointer;transition:transform .16s,box-shadow .16s}.shortcuts button:hover{transform:translateY(-2px);box-shadow:0 12px 24px rgba(48,63,77,.1)}.shortcuts i{justify-self:end;color:#9aa6b2;font-style:normal}.shortcut-icon{display:grid;place-items:center;width:31px;height:31px;border-radius:9px;font-size:18px}.shortcut-icon--rose{background:#ffeaeb;color:#ce5360}.shortcut-icon--orange{background:#fff1dc;color:#e2841e}.shortcut-icon--blue{background:#e8f0f8;color:#3d607f}.renewals{padding:18px}.renewals__header{display:flex;align-items:center;justify-content:space-between}.renewals__header strong{display:grid;place-items:center;min-width:36px;height:36px;border-radius:11px;background:#fff1df;color:#d16a13;font-size:14px}.renewals__filter{display:grid;grid-template-columns:1fr auto;align-items:center;gap:8px;margin:18px 0 12px;color:var(--text-muted);font-size:12px}.renewals__filter b{color:#344151}.renewals__filter input{grid-column:1/2;width:100%;accent-color:#e9771d}.renewals__filter output{grid-column:2;grid-row:1/3;display:grid;place-items:center;width:29px;height:29px;border-radius:8px;background:#f5f7f9;color:#405061;font-size:12px;font-weight:800}.renewals__list{border-top:1px solid #edf0f2}.renewal-item{display:grid;grid-template-columns:43px minmax(0,1fr) auto;align-items:center;gap:6px;width:100%;padding:11px 0;border:0;border-bottom:1px solid #edf0f2;background:transparent;text-align:left;cursor:pointer}.renewal-item:hover span{color:#d3660d}.renewal-item b{font-size:11px;color:#d66b13}.renewal-item span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#354350;font-size:12px;font-weight:750;transition:color .16s}.renewal-item small{padding:3px 5px;border-radius:5px;background:#f1f4f6;color:#768491;font-size:10px;font-weight:800}.renewal-item small.today{background:#fff0e7;color:#d4630c}.empty{padding:19px 0;color:var(--text-muted);font-size:12px;text-align:center}.text-button{margin-top:12px;padding:0;border:0;background:transparent;color:#d2660d;font-size:12px;font-weight:850;cursor:pointer}.text-button span{margin-left:4px}.dashboard__main{min-width:0}.chart-panel{height:100%;min-height:514px;padding:27px 29px}.chart-panel__header{display:flex;align-items:flex-start;justify-content:space-between;gap:18px}.chart-controls{display:flex;gap:8px}.chart-controls select,.chart-controls input{height:37px;max-width:120px;padding:0 10px;border:1px solid #e4e8eb;border-radius:9px;background:#fbfcfd;color:#41505d;font-size:12px;font-weight:700;outline-color:var(--accent)}.kpis{display:flex;align-items:stretch;gap:30px;margin:31px 0 25px}.kpis>div{position:relative;padding-left:14px}.kpis p{color:var(--text-muted);font-size:11px}.kpis strong{display:block;margin-top:2px;color:#2b3947;font-size:20px;letter-spacing:-.04em}.kpis__marker{position:absolute;top:5px;left:0;width:7px;height:7px;border-radius:50%}.kpis__marker--green,.bar--received,.legend--received{background:#259b72}.kpis__marker--amber,.bar--forecast,.legend--forecast{background:#f1b968}.kpis__difference{margin-left:auto;padding:0!important;text-align:right}.kpis__difference strong{color:#d06a15}.chart{height:288px;display:grid;grid-template-columns:repeat(16,minmax(0,1fr));align-items:end;gap:7px;padding:15px 2px 0;border-bottom:1px solid #e5e9ed;background:repeating-linear-gradient(to bottom,transparent 0,transparent 71px,rgba(45,60,74,.055) 72px)}.chart--year{grid-template-columns:repeat(12,minmax(0,1fr))}.chart__column{height:100%;display:grid;grid-template-rows:1fr 21px;gap:7px;text-align:center}.chart__bars{display:flex;align-items:end;justify-content:center;gap:3px;height:100%}.bar{width:min(14px,37%);border-radius:5px 5px 1px 1px;transition:height .25s}.bar--forecast{opacity:.85}.chart__column small{color:#8996a2;font-size:10px}.chart-legend{display:flex;gap:19px;margin-top:17px;color:#6e7d89;font-size:11px;font-weight:700}.chart-legend span{display:inline-flex;align-items:center;gap:6px}.legend{width:8px;height:8px;border-radius:3px}@media(max-width:1020px){.dashboard__content{grid-template-columns:310px minmax(0,1fr)}.chart-panel{padding:24px}}@media(max-width:840px){.dashboard__content{grid-template-columns:1fr}.dashboard__sidebar{grid-template-columns:1fr 1fr}.contract-search,.renewals{grid-column:span 2}.chart-panel{min-height:460px}}@media(max-width:560px){.dashboard__header{align-items:flex-start;margin-bottom:20px}.dashboard h1{font-size:26px}.button-primary{padding:10px 11px;font-size:12px;white-space:nowrap}.dashboard__sidebar{grid-template-columns:1fr}.contract-search,.renewals{grid-column:auto}.chart-panel{min-height:440px;padding:19px}.chart-panel__header{display:block}.chart-controls{margin-top:15px}.kpis{gap:16px;margin:23px 0}.kpis strong{font-size:15px}.chart{height:245px;gap:3px}.chart__column small{font-size:8px}.chart-legend{gap:11px;font-size:10px}.shortcuts button{min-height:98px}}
.dashboard__content { align-items: stretch; }

@media (min-width: 841px) {
  .dashboard__sidebar {
    grid-template-rows: auto auto minmax(0, 1fr);
  }

  .renewals {
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .renewals__list {
    flex: 1;
  }
}

.contract-search {
  position: relative;
}

.contract-search .contract-search__create {
  position: absolute;
  top: 14px;
  right: 14px;
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  padding: 0;
  border: 1px solid #e4e8eb;
  border-radius: 10px;
  background: #fff;
  color: #d66b13;
  font-size: 22px;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
}

.contract-search__create:hover {
  border-color: #df7b28;
  background: #fff3e7;
}
</style>
