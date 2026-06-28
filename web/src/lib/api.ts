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

export type RunJob = {
  job_id: string
  target: string
  n: number
  concurrency: number
  status: string
  created_count: number
  conflict_count: number
  attempt_count: number
  started_at: string
  finished_at: string | null
  duration_ms: number | null
  error: string | null
}

export async function startRun(spec: { target: string; n: number; concurrency: number }): Promise<void> {
  const job_id = crypto.randomUUID()
  const res = await fetch('/api/runner/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_id, ...spec }),
  })
  if (!res.ok) throw new Error(`startRun failed: ${res.status}`)
}

export async function listRuns(): Promise<RunJob[]> {
  const res = await fetch('/api/runner/runs')
  if (!res.ok) throw new Error(`listRuns failed: ${res.status}`)
  return res.json() as Promise<RunJob[]>
}
