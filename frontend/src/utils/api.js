import { supabase } from './supabase'

export async function apiRequest(endpoint, options = {}) {
  // 1. Get the current active session
  const { data: { session } } = await supabase.auth.getSession()
  const token = session?.access_token

  // 2. Set up headers, mixing in the Bearer token if it exists
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  // 3. Execute the fetch request via your Vite proxy route
  const response = await fetch(endpoint, {
    ...options,
    headers,
  })

  if (!response.ok) {
    if (response.status === 401) {
      // Handle expired session / unauthorized state here if needed
    }
    throw new Error(`API Error: ${response.statusText}`)
  }

  return response.json()
}

// Usage Example inside a Chat component:
// const data = await apiRequest('/chat-history')