# ASM Multi-Instrument Dashboard

AWS Cloudscape Design-based dashboard for visualizing ASM data from multiple instruments.

## Features

- **Multi-Instrument Support**: View data from Nova FLEX2, EndoScan-V, Wyatt ASTRA
- **Real-Time KPIs**: Total samples, validation rate, processing time
- **Interactive Charts**: pH trends, metabolite levels (glucose, lactate)
- **Data Table**: Sortable, filterable sample data with validation status
- **AWS Cloudscape Design**: Professional AWS-style UI components

## Quick Start

### Install Dependencies
```bash
cd dashboard
npm install
```

### Run Development Server
```bash
npm run dev
```

Open http://localhost:3000

### Build for Production
```bash
npm run build
```

## Architecture

```
dashboard/
├── src/
│   ├── main.jsx          # React entry point
│   └── App.jsx           # Main dashboard component
├── index.html            # HTML template
├── package.json          # Dependencies
└── vite.config.js        # Vite configuration
```

## Components

### KPI Cards
- Total Samples
- Valid ASM Files (with validation rate)
- Active Instruments
- Average Processing Time

### Charts
- **pH Trends**: Line chart showing pH values across samples
- **Metabolite Levels**: Bar chart comparing glucose and lactate

### Data Table
- Sample ID, Instrument, Date
- pH, pO2, pCO2 measurements
- Glucose, Lactate levels
- Validation status badge

## Integration

### Connect to ATaaS API
Update `loadDemoData()` in `App.jsx`:

```javascript
const response = await fetch('https://your-api.com/asm-data')
const data = await response.json()
setAsmData(data)
```

### Real-Time Updates
Add WebSocket connection:

```javascript
const ws = new WebSocket('wss://your-api.com/stream')
ws.onmessage = (event) => {
  const newSample = JSON.parse(event.data)
  setAsmData(prev => [...prev, newSample])
}
```

## Deployment

### AWS Amplify
```bash
npm run build
# Upload dist/ folder to Amplify
```

### S3 + CloudFront
```bash
npm run build
aws s3 sync dist/ s3://your-bucket/
aws cloudfront create-invalidation --distribution-id XXX --paths "/*"
```

## Customization

### Add New Instrument
Update `instruments` array in `App.jsx`:

```javascript
const instruments = [
  { label: 'Your Instrument', value: 'your_instrument' }
]
```

### Add New Chart
Import Recharts component and add to Grid:

```javascript
import { ScatterChart, Scatter } from 'recharts'

<Container header={<Header variant="h2">Your Chart</Header>}>
  <ResponsiveContainer width="100%" height={300}>
    <ScatterChart data={chartData}>
      {/* Chart configuration */}
    </ScatterChart>
  </ResponsiveContainer>
</Container>
```

## Use Case Alignment

This dashboard addresses **Merck Use Case 1: Multi-Instrument Visualization**

✅ Single dashboard for multiple instruments  
✅ Cross-instrument analytics (pH, metabolites)  
✅ Real-time data display  
✅ Validation status tracking  
✅ Professional AWS UI  

## Next Steps

1. Connect to ATaaS API endpoints
2. Add authentication (AWS Cognito)
3. Implement real-time WebSocket updates
4. Add export functionality (CSV, PDF)
5. Create custom alerts/notifications
6. Add historical data analysis

## Technologies

- **React 18**: UI framework
- **AWS Cloudscape Design**: Component library
- **Recharts**: Data visualization
- **Vite**: Build tool
- **AWS Amplify/S3**: Deployment (recommended)
