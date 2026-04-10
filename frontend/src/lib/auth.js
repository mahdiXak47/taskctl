const ACCESS_KEY  = 'taskctl_auth_access'
const REFRESH_KEY = 'taskctl_auth_refresh'
const USERNAME_KEY = 'taskctl_auth_username'

function decodeJwtPayload(token) {
  try {
    const part = token.split('.')[1]
    if (!part) return null
    const b64 = part.replace(/-/g, '+').replace(/_/g, '/')
    const pad = b64.length % 4 === 0 ? '' : '='.repeat(4 - (b64.length % 4))
    return JSON.parse(atob(b64 + pad))
  } catch {
    return null
  }
}

function isAccessValid(token, skewMs = 5000) {
  if (!token) return false
  const p = decodeJwtPayload(token)
  if (!p?.exp) return false
  return p.exp * 1000 > Date.now() + skewMs
}

export async function registerUser({ firstName, lastName, username, email, password }) {
  const res = await fetch('/api/auth/register/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      first_name: firstName,
      last_name: lastName,
      username,
      email,
      password,
    }),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg =
      data.detail ||
      data.username?.[0] ||
      data.email?.[0] ||
      data.password?.[0] ||
      'Registration failed.'
    throw new Error(typeof msg === 'string' ? msg : 'Registration failed.')
  }
}

export async function loginWithPassword(username, password) {
  const res = await fetch('/api/auth/token/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = data.detail || 'Invalid username or password.'
    throw new Error(typeof msg === 'string' ? msg : 'Login failed.')
  }
  if (!data.access || !data.refresh) throw new Error('Login failed.')
  localStorage.setItem(ACCESS_KEY, data.access)
  localStorage.setItem(REFRESH_KEY, data.refresh)
  localStorage.setItem(USERNAME_KEY, username)
}

export async function refreshAccessToken() {
  const refresh = localStorage.getItem(REFRESH_KEY)
  if (!refresh) return false
  const res = await fetch('/api/auth/token/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  })
  if (!res.ok) return false
  const data = await res.json().catch(() => ({}))
  if (!data.access) return false
  localStorage.setItem(ACCESS_KEY, data.access)
  return true
}

export async function ensureSession() {
  const access = localStorage.getItem(ACCESS_KEY)
  if (isAccessValid(access)) return true
  if (await refreshAccessToken()) return true
  clearStoredToken()
  return false
}

export async function authorizedFetch(path, options = {}) {
  const ok = await ensureSession()
  if (!ok) throw new Error('Session expired.')
  const token = localStorage.getItem(ACCESS_KEY)
  const headers = { ...options.headers, Authorization: `Bearer ${token}` }
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
  if (options.body != null && !headers['Content-Type'] && !isFormData) {
    headers['Content-Type'] = 'application/json'
  }
  const res = await fetch(path, { ...options, headers })
  if (res.status === 401) {
    if (await refreshAccessToken()) {
      const retryToken = localStorage.getItem(ACCESS_KEY)
      return fetch(path, {
        ...options,
        headers: { ...options.headers, Authorization: `Bearer ${retryToken}` },
      })
    }
    clearStoredToken()
  }
  return res
}

export function getStoredUsername() {
  return localStorage.getItem(USERNAME_KEY) || ''
}

export function clearStoredToken() {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(USERNAME_KEY)
}
