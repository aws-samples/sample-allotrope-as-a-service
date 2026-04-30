// Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
// Licensed under the Apache License, Version 2.0 (the "License").
// You may not use this file except in compliance with the License.
// A copy of the License is located at http://aws.amazon.com/apache2.0/
// This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
// API Endpoints - Update these when deploying to a new environment
export const ENDPOINTS = {
  unifiedConverter: 'https://abc123.execute-api.us-east-1.amazonaws.com/prod',
  dvaas: 'https://abc123.execute-api.us-east-1.amazonaws.com/prod',
  customConverter: 'https://abc123.execute-api.us-east-1.amazonaws.com/prod',
  ataas: 'https://abc123.execute-api.us-east-1.amazonaws.com/prod',
  multiInstrument: 'https://abc123.execute-api.us-east-1.amazonaws.com/prod',
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
