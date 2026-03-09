# Dashboard Dynamic Data Integration Plan

## Current State

**Status**: Dashboard uses hardcoded mock data  
**Location**: `dashboard/src/VisualizationApp.jsx` (lines 15-21)  
**Data**: 6 sample records from Nova FLEX2 conversions

```javascript
const [asmData] = useState([
  { id: 1, instrument: 'Nova FLEX2', sample: 'XB21-720-0300', pH: 7.183, ... },
  { id: 2, instrument: 'Nova FLEX2', sample: 'XB22-720-0270', pH: 7.164, ... },
  // ... 4 more hardcoded samples
])
```

**Why Mock Data?**
- Demonstrates UI/UX without backend dependency
- Allows frontend development in parallel
- Shows expected data structure and visualizations

---

## Goal: Make Dashboard Dynamic

Display real-time data from converted ASM files stored in S3.

---

## Architecture Overview

```
┌─────────────────┐
│  React Dashboard│
│  (Browser)      │
└────────┬────────┘
         │ HTTP GET /api/asm-files
         ↓
┌─────────────────┐
│  API Gateway    │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Lambda Function│  ← New: ASM Data Aggregator
│  (List ASM)     │
└────────┬────────┘
         │
    ┌────┴────┐
    ↓         ↓
┌─────────┐ ┌──────────┐
│DynamoDB │ │ S3 Bucket│
│History  │ │ ASM Files│
└─────────┘ └──────────┘
```

---

## Implementation Plan

### Phase 1: Backend API (4 hours)

#### 1.1 Create Lambda Function: `asm-data-aggregator`

**Purpose**: Query S3 bucket, parse ASM files, return aggregated data

**Input**: Query parameters (optional)
- `instrument` - Filter by instrument type
- `start_date` - Filter by date range
- `end_date` - Filter by date range
- `limit` - Max records to return (default: 100)

**Output**: JSON array
```json
[
  {
    "id": "CONV-20260130123456",
    "instrument": "Nova FLEX2",
    "sample": "XB21-720-0300",
    "date": "2025-11-01",
    "pH": 7.183,
    "pO2": 94.5,
    "pCO2": 31.4,
    "glucose": 8.21,
    "lactate": 0.25,
    "osmolality": 302,
    "valid": true,
    "conversion_method": "custom_converter",
    "timestamp": "2026-01-30T12:34:56Z"
  }
]
```

**Implementation**:
```python
def lambda_handler(event, context):
    # 1. Query DynamoDB ConversionHistory table
    # 2. For each conversion_id, fetch ASM file from S3
    # 3. Parse ASM JSON and extract measurements
    # 4. Aggregate data into dashboard format
    # 5. Return JSON response
```

**Key Functions**:
- `list_conversions()` - Query DynamoDB
- `fetch_asm_file(s3_key)` - Get file from S3
- `parse_asm_measurements(asm_json)` - Extract pH, glucose, etc.
- `format_for_dashboard(data)` - Convert to dashboard schema

#### 1.2 Add API Gateway Endpoint

**Endpoint**: `GET /api/asm-files`  
**Query Parameters**:
- `?instrument=nova_flex2`
- `?start_date=2025-11-01`
- `?limit=50`

**Response**: JSON array of samples

#### 1.3 Update CDK Deployment

Add new Lambda and API Gateway route to `services/deploy_services.py`

---

### Phase 2: Frontend Integration (2 hours)

#### 2.1 Update VisualizationApp.jsx

**Replace hardcoded data with API call**:

```javascript
const [asmData, setAsmData] = useState([])
const [loading, setLoading] = useState(true)
const [error, setError] = useState(null)

useEffect(() => {
  fetchASMData()
}, [selectedInstrument])

const fetchASMData = async () => {
  setLoading(true)
  try {
    const params = new URLSearchParams()
    if (selectedInstrument.value !== 'all') {
      params.append('instrument', selectedInstrument.value)
    }
    
    const response = await fetch(
      `https://api-endpoint/prod/api/asm-files?${params}`
    )
    const data = await response.json()
    setAsmData(data)
  } catch (err) {
    setError(err.message)
  } finally {
    setLoading(false)
  }
}
```

#### 2.2 Add Loading & Error States

```javascript
if (loading) return <Spinner />
if (error) return <Alert type="error">{error}</Alert>
```

#### 2.3 Add Refresh Button

```javascript
<Button onClick={fetchASMData} iconName="refresh">
  Refresh Data
</Button>
```

---

### Phase 3: Real-time Updates (Optional - 2 hours)

#### Option A: Polling (Simple)
```javascript
// Refresh every 30 seconds
useEffect(() => {
  const interval = setInterval(fetchASMData, 30000)
  return () => clearInterval(interval)
}, [])
```

#### Option B: WebSocket (Advanced)
```javascript
const ws = new WebSocket('wss://api-endpoint/stream')
ws.onmessage = (event) => {
  const newSample = JSON.parse(event.data)
  setAsmData(prev => [newSample, ...prev])
}
```

---

## Data Flow Example

### 1. User Converts File
```
User uploads CSV → Unified Converter → Generates ASM
                                    ↓
                            Stores in S3 + DynamoDB
```

### 2. Dashboard Fetches Data
```
Dashboard → API Gateway → Lambda
                           ↓
                    Query DynamoDB (get conversion IDs)
                           ↓
                    Fetch ASM files from S3
                           ↓
                    Parse measurements (pH, glucose, etc.)
                           ↓
                    Return aggregated JSON
                           ↓
Dashboard ← Display charts and tables
```

---

## ASM Parsing Logic

**Challenge**: ASM files have nested structure, need to extract measurements

**Example ASM Structure**:
```json
{
  "solution analyzer aggregate document": {
    "solution analyzer document": [{
      "measurement aggregate document": {
        "measurement document": [
          {
            "measurement identifier": "uuid-123",
            "pH": {"value": 7.183, "unit": "pH"},
            "pO2": {"value": 94.5, "unit": "mmHg"},
            "sample document": {
              "sample identifier": "XB21-720-0300"
            }
          }
        ]
      }
    }]
  }
}
```

**Parsing Function**:
```python
def extract_measurements(asm_json):
    measurements = []
    
    # Navigate nested structure
    doc = asm_json.get('solution analyzer aggregate document', {})
    analyzer_docs = doc.get('solution analyzer document', [])
    
    for analyzer_doc in analyzer_docs:
        meas_agg = analyzer_doc.get('measurement aggregate document', {})
        meas_docs = meas_agg.get('measurement document', [])
        
        for meas in meas_docs:
            measurements.append({
                'sample': meas.get('sample document', {}).get('sample identifier'),
                'pH': meas.get('pH', {}).get('value'),
                'pO2': meas.get('pO2', {}).get('value'),
                'pCO2': meas.get('pCO2', {}).get('value'),
                # ... extract other fields
            })
    
    return measurements
```

---

## Effort Estimate

| Task | Time | Complexity |
|------|------|------------|
| Lambda function (ASM aggregator) | 2 hours | Medium |
| API Gateway endpoint | 30 min | Low |
| CDK deployment updates | 30 min | Low |
| Frontend API integration | 1 hour | Low |
| Loading/error states | 30 min | Low |
| Refresh functionality | 30 min | Low |
| Testing & debugging | 1 hour | Medium |
| **Total** | **6 hours** | **Medium** |

**Optional Enhancements** (+2-4 hours):
- Real-time WebSocket updates
- Advanced filtering (date range, validation status)
- Export to CSV functionality
- Pagination for large datasets

---

## Benefits

### For Users
✅ **Real-time visibility** - See all converted files immediately  
✅ **No manual updates** - Data refreshes automatically  
✅ **Historical analysis** - View trends over time  
✅ **Multi-instrument view** - Compare across instruments  

### For System
✅ **Scalable** - Handles thousands of samples  
✅ **Maintainable** - Single source of truth (S3)  
✅ **Auditable** - All data from validated conversions  
✅ **Extensible** - Easy to add new metrics  

---

## Risks & Mitigations

### Risk 1: Large Dataset Performance
**Issue**: Fetching 1000+ ASM files could be slow  
**Mitigation**: 
- Implement pagination (limit=100)
- Cache aggregated data in DynamoDB
- Add date range filters

### Risk 2: ASM Parsing Complexity
**Issue**: Different instruments have different ASM structures  
**Mitigation**:
- Create parser for each instrument type
- Use technique detection from manifest
- Fallback to basic fields if parsing fails

### Risk 3: API Latency
**Issue**: Parsing ASM files on-demand could be slow  
**Mitigation**:
- Pre-process ASM files during conversion
- Store extracted metrics in DynamoDB
- Lambda only queries DynamoDB (fast)

---

## Recommended Approach

### Phase 1: Simple Implementation (6 hours)
1. Create Lambda to query S3 and parse ASM files
2. Add API Gateway endpoint
3. Update dashboard to fetch from API
4. Add refresh button

**Result**: Dynamic dashboard with real data

### Phase 2: Optimization (Optional - 4 hours)
1. Pre-process ASM files during conversion
2. Store metrics in DynamoDB
3. Lambda queries DynamoDB only (faster)
4. Add real-time polling

**Result**: Fast, scalable dashboard

### Phase 3: Advanced Features (Optional - 4 hours)
1. WebSocket for real-time updates
2. Advanced filtering and search
3. Export functionality
4. Historical trend analysis

**Result**: Production-ready analytics dashboard

---

## Next Steps

1. **Review this plan** with team
2. **Decide on scope** (Phase 1 only, or include Phase 2?)
3. **Allocate resources** (6 hours for Phase 1)
4. **Create Lambda function** for ASM data aggregation
5. **Update dashboard** to use API
6. **Test with real data** from conversions
7. **Deploy to production**

---

## Questions to Answer

- [ ] Do we need real-time updates or is refresh button sufficient?
- [ ] What's the expected data volume? (100s or 1000s of samples?)
- [ ] Should we pre-process ASM files or parse on-demand?
- [ ] Do we need historical data or just recent conversions?
- [ ] What filtering options are most important?

---

**Document Version**: 1.0  
**Date**: January 30, 2026  
**Status**: Ready for Review
