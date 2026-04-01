# Production Readiness — Fix Tracker

**Created:** March 27, 2026
**Purpose:** Track all hardcoded data, mock data, and non-production issues found during dashboard review before customer handoff.

---

## 🔴 Critical

### FIX-001: VisualizationApp — Entirely mock data
- **File:** `dashboard/src/VisualizationApp.jsx`
- **Issue:** Hardcoded array of 6 sample data points with real customer sample IDs. Hardcoded instrument count (3), instrument names ("Nova FLEX2, EndoScan-V, Wyatt ASTRA"), and processing time ("<1s"). No API integration — entire tab is a static demo.
- **Action:** Either connect to real API or remove/disable the tab entirely
- **Status:** [x] Fixed — Removed VisualizationApp.jsx, removed tab from CombinedApp, removed from More Tools menu. Bundle size dropped 475 KB (Recharts removed).

### FIX-002: ConverterManagementApp — Hardcoded S3 bucket with AWS account number
- **File:** `dashboard/src/ConverterManagementApp.jsx`
- **Issue:** Details modal displays `custom-converters-550129454303-us-east-1` — exposes AWS account number to customer.
- **Action:** Remove hardcoded bucket name or fetch dynamically from API
- **Status:** [x] Fixed — Removed hardcoded bucket name with AWS account number. Instructions now only show the S3 location path from the API response (DynamoDB). Portable across any AWS account.

### FIX-003: ValidationApp — Hardcoded marketing claims
- **File:** `dashboard/src/ValidationApp.jsx`
- **Issue:** "Step 3: What We Fixed" section always shows static text: "Reduced errors from X to Y", "Added regulatory compliance features", Speed "<1s", Accuracy "100%", Compliance "FDA/EMA". These are not measured — they display regardless of actual results.
- **Action:** Derive improvement metrics from actual before/after validation results, or remove the section
- **Status:** [x] Fixed — Removed Compare & Certify tab entirely. ValidationApp.jsx archived as ValidationApp.jsx.archived for future reference. "More Tools" dropdown removed.

---

## 🟡 Medium

### FIX-004: All components — Hardcoded API endpoints
- **Files:**
  - `dashboard/src/ConvertInstrumentApp.jsx` — Unified Converter endpoint
  - `dashboard/src/ValidateASMApp.jsx` — DVaaS endpoint
  - `dashboard/src/ValidationApp.jsx` — Unified Converter + DVaaS endpoints
  - `dashboard/src/ControlTowerApp.jsx` — History endpoint
  - `dashboard/src/ConverterManagementApp.jsx` — Custom Converter API endpoint
- **Issue:** API URLs are hardcoded in each component. If endpoints change, every file needs updating. Not portable across environments (dev/staging/prod).
- **Action:** Create `dashboard/src/config.js` with all endpoints. Import from there in each component.
- **Status:** [x] Fixed — Created `dashboard/src/config.js` with all 5 service endpoints. Updated ConvertInstrumentApp, ValidateASMApp, ControlTowerApp, and ConverterManagementApp to import from config. One file to update when deploying to a new environment.

### FIX-005: CombinedApp — Dead links
- **File:** `dashboard/src/CombinedApp.jsx`
- **Issue:** 
  - Documentation: `https://github.com/aws-samples/asm-transformation-service` — likely doesn't exist
  - API Documentation: `#` — goes nowhere
  - Support: `#` — goes nowhere
- **Action:** Remove dead links or point to real URLs
- **Status:** [x] Fixed — Created User Guide (`/docs/user-guide.html`) and API & Technical Guide (`/docs/api-guide.html`) hosted on same CloudFront. Both have "Export to PDF" via browser print. Removed fake GitHub and placeholder links. Resources dropdown now links to both guides.

### FIX-006: InstrumentRegistry — "Create Manifest" button does nothing
- **File:** `dashboard/src/InstrumentRegistry.jsx`
- **Issue:** "Create Manifest" button has no onClick handler. Clicking it does nothing.
- **Action:** Wire to switch to Instrument Config Creator tab with selected instrument pre-filled, or remove the button
- **Status:** [x] Fixed — Removed the button. Instrument Registry is for browsing; Instrument Config Creator tab handles config creation. No need for a redundant button.

### FIX-007: ConverterManagementApp — Hardcoded approved_by email
- **File:** `dashboard/src/ConverterManagementApp.jsx`
- **Issue:** `approved_by: 'dashboard-user@example.com'` is hardcoded. No actual user identity captured.
- **Action:** Prompt user for their email/name before approval, or integrate with Cognito for real identity
- **Status:** [x] Fixed — Added "Your Email" input field to the approval modal. Required field — Approve/Reject buttons disabled until email is entered. Email stored in DynamoDB for audit trail. Clears on modal close.

---

## 🟢 Low

### FIX-008: Multiple files — Console.log debug statements
- **Files:**
  - `dashboard/src/ValidationApp.jsx` — extensive console.log for ASM debugging
  - `dashboard/src/ManifestCreator.jsx` — `console.log('Rendering - isCustom:', ...)`
  - `dashboard/src/ConvertInstrumentApp.jsx` — `console.log('Convert result:', ...)`
- **Issue:** Debug logging visible in browser console. Not appropriate for production.
- **Action:** Remove all console.log statements or replace with conditional debug flag
- **Status:** [x] Fixed — Removed 11 debug console.log/warn statements from ConvertInstrumentApp (4), ManifestCreator (3), ValidateASMApp (1). Kept 3 console.error statements for real error handling (non-JSON response, catch blocks).

### FIX-009: ValidationApp — Duplicate TopNavigation
- **File:** `dashboard/src/ValidationApp.jsx`
- **Issue:** Has its own TopNavigation component. When accessed via "More Tools" menu in CombinedApp, it renders a duplicate header bar.
- **Action:** Remove TopNavigation and AppLayout wrapper — this component is rendered inside CombinedApp
- **Status:** [x] Closed — ValidationApp was archived in FIX-003. No longer in active codebase.

---

## Summary

| Priority | Count | Status |
|----------|-------|--------|
| 🔴 Critical | 3 | 3/3 fixed |
| 🟡 Medium | 4 | 4/4 fixed |
| 🟢 Low | 2 | 2/2 fixed |
| **Total** | **9** | **9/9 fixed** |

---

## Fix Log

| Date | Fix ID | Description | By |
|------|--------|-------------|----|
| 2026-03-27 | FIX-001 | Removed VisualizationApp (mock data tab) and Recharts dependency | Q |
| 2026-03-27 | FIX-002 | Removed hardcoded S3 bucket name with AWS account number | Q |
| 2026-03-27 | FIX-003 | Removed Compare & Certify tab (hardcoded claims). Archived for reference. | Q |
| 2026-03-27 | FIX-004 | Centralized API endpoints into config.js | Q |
| 2026-03-27 | FIX-005 | Created User Guide and API Guide pages, replaced dead links | Q |
| 2026-03-27 | FIX-006 | Removed non-functional Create Manifest button from Instrument Registry | Q |
| 2026-03-27 | FIX-007 | Replaced hardcoded email with reviewer email input in approval modal | Q |
| 2026-03-27 | FIX-008 | Removed 11 debug console.log statements, kept console.error for real errors | Q |
| 2026-03-27 | FIX-009 | Closed — ValidationApp archived in FIX-003, duplicate TopNav no longer exists | Q |
