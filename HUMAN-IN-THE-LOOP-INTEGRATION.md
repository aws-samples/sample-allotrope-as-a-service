# Human-in-the-Loop Approval Workflow - Integration Plan

## Current Status: NOT INTEGRATED ❌

The approval workflow system exists but is **completely disconnected** from the main ATaaS service.

---

## What Exists

### 1. Approval Workflow Service
**Location**: `approval-system/backend/lambda_function.py`

**Capabilities**:
- ✅ `submit_for_review()` - Submit converter for human review
- ✅ `get_pending()` - List converters awaiting approval
- ✅ `approve()` - Approve converter with electronic signature
- ✅ `reject()` - Reject converter with feedback
- ✅ `get_approved()` - List approved converters in library

### 2. Storage Infrastructure
- **DynamoDB Table**: `ConverterApprovals` - tracks status (PENDING_REVIEW, APPROVED, REJECTED)
- **S3 Pending Bucket**: `asm-pending-converters` - stores code awaiting review
- **S3 Approved Bucket**: `asm-approved-converters` - stores approved converters

### 3. Frontend Dashboard
**Location**: `approval-system/frontend/approval-dashboard.html`

**Features**:
- View pending converters
- Review generated code
- Electronic signature for approval
- Rejection with feedback
- Browse approved library

### 4. Deployment Stack
**Location**: `approval-system/deploy_approval.py`

**Status**: ✅ Ready to deploy (CDK stack complete)

---

## Integration Gaps

### Gap 1: ATaaS Doesn't Submit to Approval
**Current Flow**:
```
ATaaS → Generate Converter → Return to User
```

**Problem**: Generated converter code is returned in API response but never submitted for approval workflow.

**File**: `services/ataas/lambda_function.py`

**Missing Code** (line ~50, after converter generation):
```python
# After generating converter code
converter_code = generate_converter_with_claude(file_content, file_analysis)

# MISSING: Submit to approval workflow
approval_result = submit_to_approval_workflow({
    'code': converter_code['code'],
    'language': converter_code['language'],
    'filename': converter_code['filename'],
    'format': analysis.get('file_format'),
    'instrument_type': analysis.get('instrument_type'),
    'conversion_id': conversion_id,
    'file_analysis': file_analysis
})
```

### Gap 2: No Approval Status Check
**Problem**: System doesn't verify if converter is approved before using it.

**Missing**: Function to check if converter exists in approved library before using.

**Needed**:
```python
def get_approved_converter(instrument_type, file_format):
    """Check if approved converter exists for this instrument/format"""
    # Query ConverterApprovals table
    # Filter by status=APPROVED, instrument_type, file_format
    # Return converter code if found
    pass
```

### Gap 3: Separate Storage Systems
**Problem**: 
- ATaaS stores in `asm-converted-files` bucket
- Approval system stores in `asm-pending-converters` and `asm-approved-converters`
- No shared references

**Solution**: Use approval system buckets as source of truth.

### Gap 4: No Workflow Enforcement
**Problem**: No policy to enforce "approved converters only" in production.

**Needed**: Configuration flag to require approval before converter can be used.

---

## Desired Flow

### Scenario 1: New Unknown Instrument (Requires Approval)
```
1. User uploads file → ATaaS
2. ATaaS analyzes file → Identifies unknown instrument
3. ATaaS generates converter code → Claude
4. ATaaS submits converter → Approval Workflow (PENDING_REVIEW)
5. ATaaS returns: "Converter generated, pending approval. Conversion ID: CONV-xxx"
6. Human reviewer → Approval Dashboard
7. Reviewer examines code → Approves with signature
8. Converter moved to → Approved Library
9. User can now use converter → For future files
```

### Scenario 2: Known Approved Instrument (Skip Approval)
```
1. User uploads file → ATaaS
2. ATaaS analyzes file → Identifies instrument type
3. ATaaS checks → Approved Library
4. Approved converter found → Use directly
5. ATaaS converts file → Returns ASM output
6. No approval needed → Instant conversion
```

### Scenario 3: Rejected Converter (Regenerate)
```
1. Converter submitted → PENDING_REVIEW
2. Reviewer rejects → Provides feedback
3. System notifies → Original requester
4. User can request regeneration → With feedback incorporated
5. New converter submitted → PENDING_REVIEW again
```

---

## Implementation Tasks

### Task 1: Integrate ATaaS with Approval Service
**File**: `services/ataas/lambda_function.py`

**Changes**:
1. Add function to call Approval Workflow API
2. Submit generated converter after creation
3. Return approval status in response
4. Add configuration for "require_approval" mode

**Estimated Effort**: 2 hours

### Task 2: Add Approved Converter Lookup
**File**: `services/ataas/lambda_function.py`

**Changes**:
1. Before generating new converter, check approved library
2. Query DynamoDB for matching instrument_type + file_format
3. If found, download from S3 and use
4. If not found, generate new and submit for approval

**Estimated Effort**: 2 hours

### Task 3: Unify Storage Architecture
**Files**: 
- `services/ataas/lambda_function.py`
- `services/deploy_services.py`

**Changes**:
1. Update ATaaS to use approval system buckets
2. Remove duplicate `asm-converted-files` bucket
3. Update environment variables
4. Update CDK stack

**Estimated Effort**: 1 hour

### Task 4: Deploy Approval Workflow
**File**: `approval-system/deploy_approval.py`

**Changes**:
1. Deploy CDK stack
2. Upload dashboard to S3
3. Configure API Gateway
4. Test end-to-end workflow

**Estimated Effort**: 1 hour

### Task 5: Add Workflow Enforcement
**File**: `services/ataas/lambda_function.py`

**Changes**:
1. Add environment variable: `REQUIRE_APPROVAL=true/false`
2. If true, only use approved converters
3. If false, allow direct use of generated converters (dev mode)
4. Return clear error if converter not approved

**Estimated Effort**: 1 hour

### Task 6: Update Documentation
**Files**: 
- `USER-GUIDE.md`
- `MEMORY.md`

**Changes**:
1. Document approval workflow
2. Add examples of approval process
3. Update architecture diagrams
4. Add troubleshooting guide

**Estimated Effort**: 1 hour

---

## Total Estimated Effort: 8 hours

---

## Configuration Options

### Environment Variables (ATaaS)
```bash
# Approval workflow integration
APPROVAL_WORKFLOW_API=https://xxx.execute-api.us-east-1.amazonaws.com/prod/workflow
REQUIRE_APPROVAL=true  # Enforce approval in production
AUTO_SUBMIT_FOR_APPROVAL=true  # Automatically submit generated converters

# Storage (use approval system buckets)
PENDING_CONVERTERS_BUCKET=asm-pending-converters
APPROVED_CONVERTERS_BUCKET=asm-approved-converters
```

### Deployment Modes

**Development Mode**:
- `REQUIRE_APPROVAL=false`
- Generated converters used immediately
- No approval workflow
- Fast iteration

**Production Mode**:
- `REQUIRE_APPROVAL=true`
- Only approved converters allowed
- All new converters go through review
- GxP compliant

---

## Benefits of Integration

1. **Regulatory Compliance**: GxP-compliant approval process with electronic signatures
2. **Quality Control**: Human review ensures converter accuracy
3. **Audit Trail**: Complete history of who approved what and when
4. **Reusability**: Approved converters stored in library for future use
5. **Safety**: Prevents untested converters from being used in production
6. **Feedback Loop**: Rejected converters can be improved and resubmitted

---

## Testing Plan

### Test 1: Submit New Converter
1. Upload unknown instrument file to ATaaS
2. Verify converter submitted to approval workflow
3. Check DynamoDB for PENDING_REVIEW status
4. Verify code stored in pending bucket

### Test 2: Approve Converter
1. Open approval dashboard
2. Review pending converter
3. Approve with electronic signature
4. Verify status changed to APPROVED
5. Verify code moved to approved bucket

### Test 3: Use Approved Converter
1. Upload same instrument file again
2. Verify ATaaS finds approved converter
3. Verify conversion uses approved code
4. Verify no new approval request created

### Test 4: Reject Converter
1. Submit converter for review
2. Reject with feedback
3. Verify status changed to REJECTED
4. Verify feedback stored in DynamoDB

### Test 5: Enforcement Mode
1. Set REQUIRE_APPROVAL=true
2. Upload file with no approved converter
3. Verify error returned
4. Verify conversion blocked

---

## Current Workaround

Until integration is complete, the approval workflow can be used manually:

1. **Generate Converter**: Call ATaaS to generate converter code
2. **Manual Submit**: Copy converter code and manually submit via approval API
3. **Review**: Use approval dashboard to review and approve
4. **Manual Deploy**: Download approved converter and deploy manually

**API Example**:
```bash
# Submit converter for review
curl -X POST https://approval-api/workflow \
  -H "Content-Type: application/json" \
  -d '{
    "action": "submit_for_review",
    "code": "...",
    "language": "python",
    "filename": "converter.py",
    "format": "CSV",
    "instrument_type": "solution_analyzer"
  }'
```

---

## Next Steps

1. **Decision**: Determine if approval workflow integration is priority
2. **Timeline**: Schedule 8-hour implementation window
3. **Deploy**: Deploy approval workflow stack first (standalone)
4. **Integrate**: Connect ATaaS to approval workflow
5. **Test**: Run complete end-to-end testing
6. **Document**: Update user guides and architecture docs

---

## Related Files

- `approval-system/backend/lambda_function.py` - Approval service
- `approval-system/frontend/approval-dashboard.html` - Review UI
- `approval-system/deploy_approval.py` - CDK deployment
- `services/ataas/lambda_function.py` - ATaaS service (needs integration)
- `services/deploy_services.py` - Main CDK stack (needs update)

---

## Questions to Answer

1. **Priority**: Is approval workflow needed for customer demo?
2. **Mode**: Should we run in development mode (no approval) or production mode (approval required)?
3. **Timeline**: When should this integration be completed?
4. **Scope**: Should all converters require approval, or only AI-generated ones?
5. **Reviewers**: Who will be the authorized reviewers in the system?

---

**Status**: Ready for implementation when prioritized
**Last Updated**: January 2026
