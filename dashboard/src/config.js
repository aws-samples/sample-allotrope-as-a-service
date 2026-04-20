// API Endpoints - Update these when deploying to a new environment
export const ENDPOINTS = {
  unifiedConverter: 'https://tqzatn5bse.execute-api.us-east-1.amazonaws.com/prod',
  dvaas: 'https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod',
  customConverter: 'https://tfv79s08rl.execute-api.us-east-1.amazonaws.com/prod',
  ataas: 'https://3dbnsq6w6h.execute-api.us-east-1.amazonaws.com/prod',
  multiInstrument: 'https://6uogqq4zb5.execute-api.us-east-1.amazonaws.com/prod',
}

// API Key - set after deployment if API key protection is enabled
// Retrieve with: aws apigateway get-api-key --api-key <id> --include-value
export const API_KEY = ''

// Helper to build headers for API calls
export function apiHeaders(contentType = 'application/json') {
  const headers = { 'Content-Type': contentType }
  if (API_KEY) headers['x-api-key'] = API_KEY
  const token = localStorage.getItem('asm_token')
  if (token) headers['Authorization'] = `Bearer ${token}`
  return headers
}

// Wrapper around fetch that adds auth headers and handles 401 (expired/invalid token)
export async function authFetch(url, options = {}) {
  const opts = { ...options, headers: { ...apiHeaders(), ...options.headers } }
  const response = await fetch(url, opts)
  if (response.status === 401 || response.status === 403) {
    localStorage.removeItem('asm_token')
    localStorage.removeItem('asm_user')
    window.location.reload()
    throw new Error('Session expired. Please log in again.')
  }
  return response
}
