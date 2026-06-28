export type UserRead = {
  id: string
  name: string
  created_at: string
}

export async function createUser(name: string): Promise<UserRead> {
  const res = await fetch('/api/app/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) throw new Error(`createUser failed: ${res.status}`)
  return res.json() as Promise<UserRead>
}

export async function listUsers(limit: number, offset: number): Promise<UserRead[]> {
  const res = await fetch(`/api/app/users?limit=${limit}&offset=${offset}`)
  if (!res.ok) throw new Error(`listUsers failed: ${res.status}`)
  return res.json() as Promise<UserRead[]>
}
