import { useState } from 'react'
import AppLayout from '@cloudscape-design/components/app-layout'
import TopNavigation from '@cloudscape-design/components/top-navigation'
import Tabs from '@cloudscape-design/components/tabs'
import '@cloudscape-design/global-styles/index.css'

// Import all components
import ValidationApp from './ValidationApp'
import VisualizationApp from './VisualizationApp'
import ManifestCreator from './ManifestCreator'
import InstrumentRegistry from './InstrumentRegistry'

function CombinedApp() {
  const [activeTab, setActiveTab] = useState('validation')

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
          <Tabs
            activeTabId={activeTab}
            onChange={({ detail }) => setActiveTab(detail.activeTabId)}
            tabs={[
              {
                id: 'validation',
                label: 'Validation & Certification',
                content: <ValidationApp />
              },
              {
                id: 'visualization',
                label: 'Data Visualization',
                content: <VisualizationApp />
              },
              {
                id: 'manifest',
                label: 'Manifest Creator',
                content: <ManifestCreator />
              },
              {
                id: 'registry',
                label: 'Instrument Registry',
                content: <InstrumentRegistry />
              }
            ]}
          />
        }
      />
    </>
  )
}

export default CombinedApp
