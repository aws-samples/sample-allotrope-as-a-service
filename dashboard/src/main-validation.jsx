import React from 'react'
import ReactDOM from 'react-dom/client'
import ValidationApp from './ValidationApp'
import '@cloudscape-design/global-styles/index.css'

// Use ValidationApp for Use Case 2 demo
// Switch to App for Use Case 1 (multi-instrument visualization)
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ValidationApp />
  </React.StrictMode>
)
