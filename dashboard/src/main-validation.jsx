// Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
// Licensed under the Apache License, Version 2.0 (the "License").
// You may not use this file except in compliance with the License.
// A copy of the License is located at http://aws.amazon.com/apache2.0/
// This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
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
