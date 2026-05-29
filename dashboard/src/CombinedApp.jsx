// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { useState } from 'react'
import AppLayout from '@cloudscape-design/components/app-layout'
import TopNavigation from '@cloudscape-design/components/top-navigation'
import Tabs from '@cloudscape-design/components/tabs'
import Button from '@cloudscape-design/components/button'
import SpaceBetween from '@cloudscape-design/components/space-between'
import '@cloudscape-design/global-styles/index.css'

// Import all components
import LoginPage from './LoginPage'
import ValidateASMApp from './ValidateASMApp'
import ConvertInstrumentApp from './ConvertInstrumentApp'
import ControlTowerApp from './ControlTowerApp'
import ManifestCreator from './ManifestCreator'
import InstrumentRegistry from './InstrumentRegistry'
import ConverterManagementApp from './ConverterManagementApp'
import ValidationRulesApp from './ValidationRulesApp'
import GenerateConverterApp from './GenerateConverterApp'

function CombinedApp() {
  const [activeTab, setActiveTab] = useState('convert-instrument')
  const [user, setUser] = useState(localStorage.getItem('asm_user'))

  const handleLogout = () => {
    localStorage.removeItem('asm_token')
    localStorage.removeItem('asm_user')
    setUser(null)
  }

  if (!user) {
    return <LoginPage onLogin={(email) => setUser(email)} />
  }

  // Define all tabs including hidden ones
  const allTabs = [
    {
      id: 'convert-instrument',
      label: 'Convert Instrument File',
      content: <ConvertInstrumentApp />,
      visible: true
    },
    {
      id: 'validate-asm',
      label: 'Validate ASM File',
      content: <ValidateASMApp />,
      visible: true
    },
    {
      id: 'control-tower',
      label: 'Control Tower',
      content: <ControlTowerApp />,
      visible: true
    },
    {
      id: 'manifest',
      label: 'Instrument Config Creator',
      content: <ManifestCreator />,
      visible: true
    },
    {
      id: 'registry',
      label: 'Instrument Registry',
      content: <InstrumentRegistry />,
      visible: true
    },
    {
      id: 'converters',
      label: 'Converter Management',
      content: <ConverterManagementApp />,
      visible: true
    },
    {
      id: 'validation-rules',
      label: 'Validation Rules',
      content: <ValidationRulesApp />,
      visible: true
    },
    {
      id: 'generate-converter',
      label: 'AI Converter Generator',
      content: <GenerateConverterApp />,
      visible: false
    }
  ]

  // Get visible tabs for the tab bar
  const visibleTabs = allTabs.filter(tab => tab.visible)

  // Find current tab content (including hidden tabs)
  const currentTab = allTabs.find(tab => tab.id === activeTab)

  return (
    <>
      <TopNavigation
        identity={{
          href: '#',
          title: 'ASM Transformation Service',
          onFollow: (e) => { e.preventDefault(); setActiveTab('validate-asm') },
          logo: {
            src: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIGZpbGw9IiMxYTU0OTAiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjI0IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkE8L3RleHQ+PC9zdmc+',
            alt: 'ASM'
          }
        }}
        utilities={[
          {
            type: 'button',
            text: 'Documentation',
            href: '/docs/user-guide.html'
          },
          {
            type: 'menu-dropdown',
            text: 'Tools',
            onItemClick: ({ detail }) => {
              if (detail.id === 'ai-generator') setActiveTab('generate-converter')
            },
            items: [
              { id: 'ai-generator', text: 'AI Converter Generator' }
            ]
          },
          {
            type: 'menu-dropdown',
            text: 'Resources',
            items: [
              { id: 'user-guide', text: 'User Guide', href: '/docs/user-guide.html' },
              { id: 'api', text: 'API & Technical Guide', href: '/docs/api-guide.html' }
            ]
          },
          {
            type: 'menu-dropdown',
            text: user,
            onItemClick: ({ detail }) => {
              if (detail.id === 'signout') handleLogout()
            },
            items: [
              { id: 'signout', text: 'Sign out' }
            ]
          }
        ]}
      />

      <AppLayout
        navigationHide
        toolsHide
        content={
          visibleTabs.some(tab => tab.id === activeTab) ? (
            <Tabs
              activeTabId={activeTab}
              onChange={({ detail }) => setActiveTab(detail.activeTabId)}
              tabs={visibleTabs}
            />
          ) : (
            <SpaceBetween size="l">
              <Button variant="link" iconName="arrow-left" onClick={() => setActiveTab('validate-asm')}>Back to Dashboard</Button>
              {currentTab?.content}
            </SpaceBetween>
          )
        }
      />
    </>
  )
}

export default CombinedApp
