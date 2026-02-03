# ASM Validation & Certification Dashboard

Integrated dashboard for **Use Case 2**: Compare AWS-generated ASM vs Customer ASM with validation & certification.

## Features

✅ **File Upload**: Upload instrument files (CSV, XML, JSON)
✅ **Live Conversion**: Calls Unified Converter API
✅ **Before/After Comparison**: Customer ASM vs AWS-generated ASM
✅ **Validation Results**: Errors, warnings, certification status
✅ **PDF Reports**: Download certification reports for both versions
✅ **Improvement Metrics**: Speed, accuracy, compliance

## Quick Start

```bash
cd dashboard
npm install
npm run dev
```

Open http://localhost:3000

## How It Works

### Step 1: Upload File
- User uploads instrument file (e.g., Nova FLEX2 CSV)
- Dashboard reads file content

### Step 2: Convert & Validate
1. **Convert**: Calls Unified Converter API → generates ASM
2. **Validate AWS ASM**: Calls DVaaS with `comprehensive` level
3. **Load Customer ASM**: (For demo, uses sample customer file)
4. **Validate Customer ASM**: Calls DVaaS with `comprehensive` level

### Step 3: Show Comparison
- Side-by-side validation results
- Error/warning counts
- Certification status
- PDF report downloads
- Improvement summary

## API Integration

**Unified Converter**:
```
POST https://tqzatn5bse.execute-api.us-east-1.amazonaws.com/prod/convert
Body: { file_content, file_name }
```

**DVaaS Validation**:
```
POST https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate
Body: { asm_data, validation_level, use_allotropy_validator, generate_report, file_name }
```

## Use Case 2 Alignment

**Experiment 2 Requirements**:
✅ Compare AWS ASM to Customer ASM
✅ Validate against ASM schema
✅ Report findings
✅ Label as "Allotrope Validated/Certified"
✅ Generate PDF certification reports

**Stretch Goal** (Not Implemented):
❌ ASM remediation service (auto-correct non-conforming files)

## Demo Flow

1. **Upload** `demo-samples/SampleResults2025-November.csv`
2. **Click** "Convert & Validate"
3. **Watch** progress bar (10% → 100%)
4. **See** comparison:
   - Customer: INVALID (1 error - missing traceability)
   - AWS: VALID (0 errors)
5. **Download** PDF reports for both
6. **Show** improvement metrics

## Switching Between Use Cases

**Use Case 1** (Multi-Instrument Visualization):
```javascript
// In src/main.jsx
import App from './App'
ReactDOM.createRoot(document.getElementById('root')).render(<App />)
```

**Use Case 2** (Validation & Certification):
```javascript
// In src/main.jsx
import ValidationApp from './ValidationApp'
ReactDOM.createRoot(document.getElementById('root')).render(<ValidationApp />)
```

## Customer Data

For real demo, load customer's actual ASM file:
```javascript
// In ValidationApp.jsx, replace:
const customerASM = { /* sample */ }

// With:
const customerResponse = await fetch('/customer-asm/SampleResults2025-November-1.json')
const customerASM = await customerResponse.json()
```

## Next Steps

1. ✅ Test with Nova FLEX2 files
2. ✅ Generate PDF reports
3. ⏳ Add ASM remediation service (stretch goal)
4. ⏳ Deploy to AWS Amplify
5. ⏳ Add authentication

## Technologies

- React 18
- AWS Cloudscape Design
- Unified Converter API
- DVaaS API
- PDF generation (reportlab)
