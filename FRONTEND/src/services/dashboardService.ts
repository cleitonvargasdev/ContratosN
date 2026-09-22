import { apiFetch } from '@/services/http'

export type DashboardGrouping = 'dia' | 'ano'
export interface DashboardChartPoint { label: string; previsto: number; recebido: number }
export interface DashboardEndingContract { contratos_id: number; cliente_nome: string | null; data_final: string | null; valor_em_aberto: number; dias_para_finalizar: number }
export interface DashboardSummary { pontos: DashboardChartPoint[]; contratos_finalizando: DashboardEndingContract[]; total_contratos_finalizando: number }

export function getDashboardSummary(grouping: DashboardGrouping, reference: string, endingDays: number): Promise<DashboardSummary> {
  const params = new URLSearchParams({ agrupamento: grouping, referencia: reference, dias_finalizacao: String(endingDays) })
  return apiFetch<DashboardSummary>(`/dashboard/resumo?${params}`)
}
