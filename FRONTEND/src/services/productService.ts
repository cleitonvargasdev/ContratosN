import type {
  Brand,
  BrandInput,
  BrandListFilters,
  BrandListResponse,
  BrandOption,
  Product,
  ProductInput,
  ProductListFilters,
  ProductListResponse,
} from '@/models/product'
import { apiFetch } from '@/services/http'

export async function listBrands(filters: BrandListFilters): Promise<BrandListResponse> {
  const params = new URLSearchParams()
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.page_size))
  if (filters.descricao) params.set('descricao', filters.descricao)

  return apiFetch<BrandListResponse>(`/marcas/?${params.toString()}`)
}

export async function listBrandOptions(): Promise<BrandOption[]> {
  return apiFetch<BrandOption[]>('/marcas/opcoes')
}

export async function getBrandById(brandId: number): Promise<Brand> {
  return apiFetch<Brand>(`/marcas/${brandId}`)
}

export async function createBrand(payload: BrandInput): Promise<Brand> {
  return apiFetch<Brand>('/marcas/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updateBrand(brandId: number, payload: BrandInput): Promise<Brand> {
  return apiFetch<Brand>(`/marcas/${brandId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteBrand(brandId: number): Promise<void> {
  return apiFetch<void>(`/marcas/${brandId}`, { method: 'DELETE' })
}

export async function listProducts(filters: ProductListFilters): Promise<ProductListResponse> {
  const params = new URLSearchParams()
  params.set('page', String(filters.page))
  params.set('page_size', String(filters.page_size))
  if (filters.descricao) params.set('descricao', filters.descricao)
  if (typeof filters.marca_id === 'number') params.set('marca_id', String(filters.marca_id))
  if (typeof filters.ativo === 'boolean') params.set('ativo', String(filters.ativo))

  return apiFetch<ProductListResponse>(`/produtos/?${params.toString()}`)
}

export async function getProductById(productId: number): Promise<Product> {
  return apiFetch<Product>(`/produtos/${productId}`)
}

export async function createProduct(payload: ProductInput): Promise<Product> {
  return apiFetch<Product>('/produtos/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updateProduct(productId: number, payload: ProductInput): Promise<Product> {
  return apiFetch<Product>(`/produtos/${productId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteProduct(productId: number): Promise<void> {
  return apiFetch<void>(`/produtos/${productId}`, { method: 'DELETE' })
}