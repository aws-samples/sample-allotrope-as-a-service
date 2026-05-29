// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { useState } from 'react'
import Container from '@cloudscape-design/components/container'
import Header from '@cloudscape-design/components/header'
import SpaceBetween from '@cloudscape-design/components/space-between'
import FormField from '@cloudscape-design/components/form-field'
import Input from '@cloudscape-design/components/input'
import Button from '@cloudscape-design/components/button'
import Alert from '@cloudscape-design/components/alert'
import Box from '@cloudscape-design/components/box'
import Link from '@cloudscape-design/components/link'

import { ENDPOINTS } from './config'

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const handleSubmit = async () => {
    setError(null)
    setSuccess(null)
    if (!email || !password) {
      setError('Email and password are required.')
      return
    }
    if (isRegister && password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }

    setLoading(true)
    try {
      const endpoint = isRegister ? 'auth/register' : 'auth/login'
      const resp = await fetch(`${ENDPOINTS.customConverter}/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      const data = await resp.json()

      if (!resp.ok) {
        setError(data.error || 'Request failed')
        return
      }

      if (isRegister) {
        setSuccess('Account created. You can now log in.')
        setIsRegister(false)
      } else {
        localStorage.setItem('asm_token', data.token)
        localStorage.setItem('asm_user', data.email)
        onLogin(data.email)
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#f2f3f3' }}>
      <div style={{ width: '400px' }}>
        <SpaceBetween size="l">
          <Box textAlign="center">
            <Box variant="h1" color="text-label">ASM Transformation Service</Box>
          </Box>

          <Container header={<Header variant="h2">{isRegister ? 'Create Account' : 'Sign In'}</Header>}>
            <SpaceBetween size="m">
              {error && <Alert type="error" dismissible onDismiss={() => setError(null)}>{error}</Alert>}
              {success && <Alert type="success" dismissible onDismiss={() => setSuccess(null)}>{success}</Alert>}

              <FormField label="Email">
                <Input
                  type="email"
                  value={email}
                  onChange={({ detail }) => setEmail(detail.value)}
                  placeholder="you@company.com"
                  onKeyDown={({ detail }) => { if (detail.key === 'Enter') handleSubmit() }}
                />
              </FormField>

              <FormField label="Password" constraintText={isRegister ? 'Minimum 8 characters' : ''}>
                <Input
                  type="password"
                  value={password}
                  onChange={({ detail }) => setPassword(detail.value)}
                  placeholder="Enter password"
                  onKeyDown={({ detail }) => { if (detail.key === 'Enter') handleSubmit() }}
                />
              </FormField>

              <Button variant="primary" fullWidth loading={loading} onClick={handleSubmit}>
                {isRegister ? 'Create Account' : 'Sign In'}
              </Button>

              <Box textAlign="center">
                {isRegister ? (
                  <span>Already have an account? <Link onFollow={() => { setIsRegister(false); setError(null); setSuccess(null) }}>Sign in</Link></span>
                ) : (
                  <span>Need an account? <Link onFollow={() => { setIsRegister(true); setError(null); setSuccess(null) }}>Create one</Link></span>
                )}
              </Box>
            </SpaceBetween>
          </Container>
        </SpaceBetween>
      </div>
    </div>
  )
}
