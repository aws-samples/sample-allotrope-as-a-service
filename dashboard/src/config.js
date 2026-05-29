// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

// API Endpoints - Update these when deploying to a new environment
export const ENDPOINTS = {
  unifiedConverter: 'https://uv53e7sj4k.execute-api.us-east-1.amazonaws.com/prod',
  dvaas: 'https://8oujzjf3qg.execute-api.us-east-1.amazonaws.com/prod',
  customConverter: 'https://lfoeu00978.execute-api.us-east-1.amazonaws.com/prod',
  ataas: 'https://1n9k8uhjk8.execute-api.us-east-1.amazonaws.com/prod',
  multiInstrument: 'https://ji40tgsy3i.execute-api.us-east-1.amazonaws.com/prod',
}

// API Key - set after deployment if API key protection is enabled
export const API_KEY = ''

export function apiHeaders(contentType = 'application/json') {
  const headers = { 'Content-Type': contentType }
  if (API_KEY) headers['x-api-key'] = API_KEY
  const token = localStorage.getItem('asm_token')
  if (token) headers['Authorization'] = `Bearer ${token}`
  return headers
}

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
