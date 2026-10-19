import { apiFetch } from '@/services/http'

export type StockKind = 'entrada' | 'baixa' | 'ajuste' | 'devolucao'
export const stockReasons: Record<StockKind, string[]> = {
  entrada: ['Estoque inicial', 'Compra', 'Outros'],
  baixa: ['Quebra', 'Extravio', 'Furto ou roubo', 'Desgaste', 'Descarte', 'Outros'],
  ajuste: ['Inventário', 'Correção de lançamento', 'Outros'],
  devolucao: ['Devolução de cliente'],
}
export interface StockInput {
  operacao_id: string
  tipo: StockKind
  condicao: 'novo' | 'usado'
  quantidade: number
  motivo: string
  observacao: string
  versao_esperada?: number
  item_id?: number
}
export interface StockMovement {
  movimento_id: number
  criado_em: string
  tipo: string
  condicao: string
  quantidade: number
  saldo_antes: number
  saldo_depois: number
  motivo: string
  observacao: string | null
  usuario_nome: string
  item_id: number | null
}
export interface StockHistory {
  items: StockMovement[]
  total: number
  page: number
  page_size: number
}
export function getStockHistory(productId: number, page: number) {
  return apiFetch<StockHistory>(`/produtos/${productId}/estoque?page=${page}&page_size=10`)
}
export function moveStock(productId: number, payload: StockInput) {
  return apiFetch<StockMovement>(`/produtos/${productId}/estoque`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
  })
}
