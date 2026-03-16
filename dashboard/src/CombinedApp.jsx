import { useState } from 'react'
import AppLayout from '@cloudscape-design/components/app-layout'
import TopNavigation from '@cloudscape-design/components/top-navigation'
import Tabs from '@cloudscape-design/components/tabs'
import '@cloudscape-design/global-styles/index.css'

// Import all components
import ValidationApp from './ValidationApp'
import ValidateASMApp from './ValidateASMApp'
import ConvertInstrumentApp from './ConvertInstrumentApp'
import VisualizationApp from './VisualizationApp'
import ControlTowerApp from './ControlTowerApp'
import ManifestCreator from './ManifestCreator'
import InstrumentRegistry from './InstrumentRegistry'
import ConverterManagementApp from './ConverterManagementApp'

function CombinedApp() {
  const [activeTab, setActiveTab] = useState('validate-asm')

  // Define all tabs including hidden ones
  const allTabs = [
    {
      id: 'validate-asm',
      label: 'Validate ASM File',
      content: <ValidateASMApp />,
      visible: true
    },
    {
      id: 'convert-instrument',
      label: 'Convert Instrument File',
      content: <ConvertInstrumentApp />,
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
      id: 'validation',
      label: 'Compare & Certify',
      content: <ValidationApp />,
      visible: false
    },
    {
      id: 'visualization',
      label: 'Data Visualization',
      content: <VisualizationApp />,
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
          logo: {
            src: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIGZpbGw9IiMxYTU0OTAiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjI0IiBmaWxsPSJ3aGl0ZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkE8L3RleHQ+PC9zdmc+',
            alt: 'ASM'
          }
        }}
        utilities={[
          {
            type: 'button',
            text: 'Documentation',
            href: 'https://github.com/aws-samples/asm-transformation-service'
          },
          {
            type: 'menu-dropdown',
            text: 'More Tools',
            items: [
              { 
                id: 'compare', 
                text: 'Compare & Certify', 
                href: '#',
                onFollow: (e) => {
                  e.preventDefault();
                  setActiveTab('validation');
                }
              },
              { 
                id: 'visualization', 
                text: 'Data Visualization', 
                href: '#',
                onFollow: (e) => {
                  e.preventDefault();
                  setActiveTab('visualization');
                }
              }
            ]
          },
          {
            type: 'menu-dropdown',
            text: 'Resources',
            items: [
              { id: 'api', text: 'API Documentation', href: '#' },
              { id: 'support', text: 'Support', href: '#' },
              { id: 'github', text: 'GitHub', href: 'https://github.com/aws-samples/asm-transformation-service' }
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
            currentTab?.content
          )
        }
      />
    </>
  )
}

export default CombinedApp
