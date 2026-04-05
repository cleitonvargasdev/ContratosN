import type { PermissionResource, Profile, ProfileInput } from '@/models/accessControl'
import { apiFetch } from '@/services/http'

export async function listProfiles(term?: string): Promise<Profile[]> {
  const params = new URLSearchParams()
  if (term) params.set('term', term)
  return apiFetch<Profile[]>(`/acesso/perfis${params.size ? `?${params.toString()}` : ''}`)
}

export async function getProfileById(profileId: number): Promise<Profile> {
  return apiFetch<Profile>(`/acesso/perfis/${profileId}`)
}

export async function createProfile(payload: ProfileInput): Promise<Profile> {
  return apiFetch<Profile>('/acesso/perfis', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function updateProfile(profileId: number, payload: ProfileInput): Promise<Profile> {
  return apiFetch<Profile>(`/acesso/perfis/${profileId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export async function deleteProfile(profileId: number): Promise<void> {
  return apiFetch<void>(`/acesso/perfis/${profileId}`, { method: 'DELETE' })
}

export async function listPermissionResources(): Promise<PermissionResource[]> {
  return apiFetch<PermissionResource[]>('/acesso/recursos')
}
