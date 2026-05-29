// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

import { useState, useEffect } from 'react'
import Container from '@cloudscape-design/components/container'
import Header from '@cloudscape-design/components/header'
import SpaceBetween from '@cloudscape-design/components/space-between'
import Box from '@cloudscape-design/components/box'
import Badge from '@cloudscape-design/components/badge'
import Button from '@cloudscape-design/components/button'
import FileUpload from '@cloudscape-design/components/file-upload'
import Alert from '@cloudscape-design/components/alert'
import ProgressBar from '@cloudscape-design/components/progress-bar'
import ColumnLayout from '@cloudscape-design/components/column-layout'
import ExpandableSection from '@cloudscape-design/components/expandable-section'
import FormField from '@cloudscape-design/components/form-field'
import Select from '@cloudscape-design/components/select'

import { ENDPOINTS, authFetch } from './config'

function ValidateASMApp() {
  const [file, setFile] = useState([])
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [validation, setValidation] = useState(null)
  const [error, setError] = useState(null)
  const [asmData, setAsmData] = useState(null)
  const [validationLevel, setValidationLevel] = useState({ label: 'Comprehensive', value: 'comprehensive', description: 'Schema + supplementary checks (recommended)' })

  const [enabledRuleSets, setEnabledRuleSets] = useState([])

  // Fetch enabled rule sets from API on mount
  useEffect(() => {
    authFetch(`${ENDPOINTS.customConverter}/rule-sets`)
      .then(r => r.json())
      .then(data => setEnabledRuleSets((data.rule_sets || []).filter(rs => rs.enabled)))
      .catch(() => {})
  }, [])

  const handleValidate = async () => {
    if (!file.length) return
    
    setLoading(true)
    setProgress(10)
    setError(null)
    setValidation(null)

    try {
      // Read ASM file
      const fileContent = await file[0].text()
      setProgress(30)
      
      const asmData = JSON.parse(fileContent)
      setAsmData(asmData)
      setProgress(50)

      // Use rule sets fetched from API
      const enabledForRequest = enabledRuleSets

      // Validate ASM
      const response = await authFetch(`${ENDPOINTS.dvaas}/validate`, {
        method: 'POST',
        body: JSON.stringify({
          asm_data: asmData,
          validation_level: validationLevel.value,
          rule_sets: enabledForRequest.length > 0 ? enabledForRequest : [],
          generate_report: true,
          file_name: file[0].name
        })
      })
      
      const result = await response.json()
      
      if (!response.ok) {
        throw new Error(result.error || 'Validation failed')
      }
      
      setValidation(result)
      setProgress(100)

    } catch (err) {
      console.error('Error:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const downloadPDF = () => {
    if (!validation?.certification_report?.data) return
    
    const pdfData = atob(validation.certification_report.data)
    const bytes = new Uint8Array(pdfData.length)
    for (let i = 0; i < pdfData.length; i++) {
      bytes[i] = pdfData.charCodeAt(i)
    }
    const blob = new Blob([bytes], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `validation_report_${file[0]?.name || 'asm'}.pdf`
    a.click()
  }

  const extractAsmSnippet = (asm, key) => {
    if (!asm) return null
    const search = (obj, target) => {
      if (!obj || typeof obj !== 'object') return null
      if (target in obj) return { [target]: obj[target] }
      for (const v of Object.values(obj)) {
        const found = search(v, target)
        if (found) return found
      }
      if (Array.isArray(obj)) {
        for (const item of obj) {
          const found = search(item, target)
          if (found) return found
        }
      }
      return null
    }
    return search(asm, key)
  }

  const getRecommendations = (errors, warnings) => {
    const recommendations = []

    if (errors?.some(e => e.includes('data source') || e.includes('traceability')) ||
        warnings?.some(w => w.includes('data source') || w.includes('traceability'))) {
      const snippet = extractAsmSnippet(asmData, 'calculated data aggregate document')
        || extractAsmSnippet(asmData, 'calculated data document')
      recommendations.push({
        issue: 'Missing Data Source Traceability',
        severity: 'high',
        description: 'Calculated values are not linked to their source measurements.',
        fix: 'Add a "data source aggregate document" inside each calculated data document that references the measurement identifiers used in the calculation.',
        sourceSnippet: snippet,
        example: `"calculated data document": [{
  "calculated data identifier": "calc-1",
  "calculated data name": "temperature corrected pH",
  "calculated result": {"value": 7.189, "unit": "pH"},
  "data source aggregate document": {
    "data source document": [{
      "data source identifier": "measurement-1",
      "data source feature": "pH measurement"
    }]
  }
}]`
      })
    }

    if (errors?.some(e => e.includes('is a required property'))) {
      const missing = errors.filter(e => e.includes('is a required property')).map(e => {
        const match = e.match(/"([^"]+)" is a required property/)
        return match ? match[1] : null
      }).filter(Boolean)
      const snippet = missing.length > 0 ? extractAsmSnippet(asmData, missing[0]) : null
      recommendations.push({
        issue: 'Missing Required Properties',
        severity: 'high',
        description: `The Allotrope schema requires these fields: ${missing.join(', ')}`,
        fix: 'Add the missing required fields to your ASM document at the locations indicated in the errors above.',
        sourceSnippet: snippet,
        example: missing.includes('measurement identifier') ? `"measurement identifier": "measurement-1"` : ''
      })
    }

    if (errors?.some(e => e.includes('manifest'))) {
      const snippet = asmData ? { '$asm.manifest': asmData['$asm.manifest'] || '(missing)' } : null
      recommendations.push({
        issue: 'Invalid or Missing Manifest',
        severity: 'high',
        description: 'The $asm.manifest field is missing or points to an invalid schema.',
        fix: 'Add a valid Allotrope manifest URL that matches your instrument type.',
        sourceSnippet: snippet,
        example: `"$asm.manifest": "http://purl.allotrope.org/manifests/solution-analyzer/REC/2025/06/solution-analyzer.manifest"`
      })
    }

    if (warnings?.some(w => w.includes('unit') || w.includes('Unit'))) {
      const snippet = extractAsmSnippet(asmData, 'measurement document')
      recommendations.push({
        issue: 'Unknown or Non-Standard Units',
        severity: 'medium',
        description: 'Some measurement units are not recognized by the Allotrope standard.',
        fix: 'Use standard SI units or Allotrope-approved unit codes. Common units: pH, mmHg, mmol/L, g/L, mOsm/kg.',
        sourceSnippet: snippet,
        example: `"pH": {"value": 7.183, "unit": "pH"}
"pO2": {"value": 94.5, "unit": "mmHg"}
"glucose": {"value": 2.5, "unit": "g/L"}`
      })
    }

    if (warnings?.some(w => w.includes('serial') || w.includes('software'))) {
      const snippet = extractAsmSnippet(asmData, 'device system document')
        || extractAsmSnippet(asmData, 'device identifier')
      recommendations.push({
        issue: 'Missing Equipment Metadata',
        severity: 'low',
        description: 'Equipment serial number or software version is missing.',
        fix: 'Add device serial number and software version to the device system document for full regulatory compliance.',
        sourceSnippet: snippet,
        example: `"device system document": {
  "device identifier": "FLEX2-2023-001",
  "equipment serial number": "FLEX2-2023-001",
  "firmware version": "6.2.1"
}`
      })
    }

    if (recommendations.length === 0 && (errors?.length > 0 || warnings?.length > 0)) {
      recommendations.push({
        issue: 'General ASM Compliance Issues',
        severity: 'medium',
        description: 'Your ASM file has validation issues that need attention.',
        fix: 'Review the errors and warnings below. Ensure your ASM file follows the Allotrope Simple Model schema for your instrument type.',
        sourceSnippet: null,
        example: 'Refer to Allotrope documentation at http://purl.allotrope.org/'
      })
    }

    return recommendations
  }

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="Upload an ASM file to validate against Allotrope standards and receive detailed feedback"
      >
        Validate ASM File
      </Header>

      {/* File Upload */}
      <Container header={<Header variant="h2">Upload ASM File</Header>}>
        <SpaceBetween size="m">
          <FileUpload
            onChange={({ detail }) => setFile(detail.value)}
            value={file}
            i18nStrings={{
              uploadButtonText: e => e ? "Choose files" : "Choose file",
              dropzoneText: e => e ? "Drop files to upload" : "Drop file to upload",
              removeFileAriaLabel: e => `Remove file ${e + 1}`,
              limitShowFewer: "Show fewer files",
              limitShowMore: "Show more files",
              errorIconAriaLabel: "Error"
            }}
            showFileLastModified
            showFileSize
            showFileThumbnail
            tokenLimit={1}
            constraintText="ASM file in JSON format (.json)"
            accept=".json"
          />

          <FormField
            label="Validation Level"
            description="Choose the strictness of validation"
          >
            <Select
              selectedOption={validationLevel}
              onChange={({ detail }) => setValidationLevel(detail.selectedOption)}
              options={[
                { label: 'Basic', value: 'basic', description: 'Schema validation only' },
                { label: 'Comprehensive', value: 'comprehensive', description: 'Schema + supplementary checks (recommended)' },
                { label: 'Certification', value: 'certification', description: 'Strict mode — warnings become errors, issues certificate if passed' }
              ]}
            />
          </FormField>

          {(() => {
            if (enabledRuleSets.length > 0) {
              return (
                <Alert type="info">
                  <strong>{enabledRuleSets.length} plugin rule set{enabledRuleSets.length > 1 ? 's' : ''} enabled:</strong>{' '}
                  {enabledRuleSets.map(rs => rs.name).join(', ')}.
                  These will run in addition to core validation. Manage rule sets on the Validation Rules tab.
                </Alert>
              )
            }
            return null
          })()}
          
          <Button
            variant="primary"
            onClick={handleValidate}
            loading={loading}
            disabled={!file.length}
          >
            Validate ASM File
          </Button>

          {loading && (
            <ProgressBar
              value={progress}
              label="Validating..."
              description="Checking ASM file against Allotrope standards..."
            />
          )}

          {error && (
            <Alert type="error" header="Validation Error">
              {error}
            </Alert>
          )}
        </SpaceBetween>
      </Container>

      {/* Validation Results */}
      {validation && (
        <>
          <Container header={<Header variant="h2">Validation Results</Header>}>
            <SpaceBetween size="m">
              <ColumnLayout columns={4} variant="text-grid">
                <div>
                  <Box variant="awsui-key-label">Schema</Box>
                  <Badge color={validation.valid ? "green" : "red"} size="large">
                    {validation.valid ? "PASS" : "FAIL"}
                  </Badge>
                </div>
                <div>
                  <Box variant="awsui-key-label">Errors</Box>
                  <Box fontSize="heading-xl" color={validation.errors?.length > 0 ? "text-status-error" : "text-status-success"}>
                    {validation.errors?.length || 0}
                  </Box>
                </div>
                <div>
                  <Box variant="awsui-key-label">Warnings</Box>
                  <Box fontSize="heading-xl" color={validation.warnings?.length > 0 ? "text-status-warning" : "text-status-success"}>
                    {validation.warnings?.length || 0}
                  </Box>
                </div>
                <div>
                  <Box variant="awsui-key-label">Validator</Box>
                  <Box>{validation.validator || 'DVaaS'}</Box>
                </div>
              </ColumnLayout>

              {validation.valid ? (
                <Alert type="success" header="Schema Validation Passed">
                  Your ASM file passes Allotrope schema validation.{validation.warnings?.length > 0 ? ` There are ${validation.warnings.length} compliance recommendation(s) below.` : ''}
                  {validation.rule_sets_applied?.length > 0 && ` Plugin rule sets applied: ${validation.rule_sets_applied.join(', ')}.`}
                </Alert>
              ) : (
                <Alert type="error" header="Validation Failed">
                  Your ASM file has {validation.errors?.length || 0} error(s). These must be fixed for the file to conform to standards.
                  {validation.rule_sets_applied?.length > 0 && ` Plugin rule sets applied: ${validation.rule_sets_applied.join(', ')}.`}
                </Alert>
              )}
            </SpaceBetween>
          </Container>

          {/* Errors */}
          {validation.errors?.length > 0 && (
            <Container header={<Header variant="h2" description="Critical issues that must be fixed">Errors ({validation.errors.length})</Header>}>
              <SpaceBetween size="s">
                {validation.errors.map((err, i) => (
                  <Alert key={i} type="error" header={`Error ${i + 1}`}>
                    {err}
                  </Alert>
                ))}
              </SpaceBetween>
            </Container>
          )}

          {/* Warnings */}
          {validation.warnings?.length > 0 && (
            <Container header={<Header variant="h2" description="Issues that should be addressed for full compliance">Compliance Recommendations ({validation.warnings.length})</Header>}>
              <SpaceBetween size="s">
                {validation.warnings.map((warn, i) => (
                  <Alert key={i} type="warning" header={`Warning ${i + 1}`}>
                    {warn}
                  </Alert>
                ))}
              </SpaceBetween>
            </Container>
          )}

          {/* Recommendations */}
          {(validation.errors?.length > 0 || validation.warnings?.length > 0) && (
            <Container header={<Header variant="h2" description="How to fix the issues found in your ASM file">Recommendations</Header>}>
              <SpaceBetween size="m">
                {getRecommendations(validation.errors, validation.warnings).map((rec, i) => (
                  <ExpandableSection
                    key={i}
                    headerText={rec.issue}
                    variant="container"
                    defaultExpanded={i === 0}
                  >
                    <SpaceBetween size="m">
                      <div>
                        <Box variant="awsui-key-label">Severity</Box>
                        <Badge color={rec.severity === 'high' ? 'red' : rec.severity === 'medium' ? 'blue' : 'grey'}>
                          {rec.severity.toUpperCase()}
                        </Badge>
                      </div>
                      
                      <div>
                        <Box variant="awsui-key-label">Description</Box>
                        <Box>{rec.description}</Box>
                      </div>
                      
                      <div>
                        <Box variant="awsui-key-label">How to Fix</Box>
                        <Box>{rec.fix}</Box>
                      </div>
                      
                      {(rec.sourceSnippet || rec.example) && (
                        <ColumnLayout columns={rec.sourceSnippet && rec.example ? 2 : 1}>
                          {rec.sourceSnippet && (
                            <div>
                              <Box variant="awsui-key-label">Your ASM (Current)</Box>
                              <Box variant="code">
                                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', background: '#fdf0f0', padding: '8px', borderRadius: '4px', fontSize: '12px' }}>
                                  {JSON.stringify(rec.sourceSnippet, null, 2)}
                                </pre>
                              </Box>
                            </div>
                          )}
                          {rec.example && (
                            <div>
                              <Box variant="awsui-key-label">Recommended (Fix)</Box>
                              <Box variant="code">
                                <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word', background: '#f0fdf0', padding: '8px', borderRadius: '4px', fontSize: '12px' }}>
                                  {rec.example}
                                </pre>
                              </Box>
                            </div>
                          )}
                        </ColumnLayout>
                      )}
                    </SpaceBetween>
                  </ExpandableSection>
                ))}
              </SpaceBetween>
            </Container>
          )}

          {/* Validation Report */}
          {validation.certification_report?.available && (
            <Container header={<Header variant="h2">Validation Report</Header>}>
              <SpaceBetween size="m">
                <Box>
                  Download a detailed PDF report of the validation results for your records and audit trail.
                </Box>
                <Button
                  variant="primary"
                  iconName="download"
                  onClick={downloadPDF}
                >
                  Download PDF Report
                </Button>
              </SpaceBetween>
            </Container>
          )}

          {/* Metrics */}
          {validation.metrics && (
            <Container header={<Header variant="h2">File Metrics</Header>}>
              <ColumnLayout columns={4} variant="text-grid">
                {validation.metrics.schema_id && (
                  <div>
                    <Box variant="awsui-key-label">Schema</Box>
                    <Box>{validation.metrics.schema_id.split('/').pop()}</Box>
                  </div>
                )}
                {validation.metrics.technique && (
                  <div>
                    <Box variant="awsui-key-label">Technique</Box>
                    <Box>{validation.metrics.technique}</Box>
                  </div>
                )}
                {validation.metrics.measurement_count !== undefined && (
                  <div>
                    <Box variant="awsui-key-label">Measurements</Box>
                    <Box>{validation.metrics.measurement_count}</Box>
                  </div>
                )}
                {validation.metrics.schema_errors !== undefined && (
                  <div>
                    <Box variant="awsui-key-label">Schema Errors</Box>
                    <Badge color={validation.metrics.schema_errors > 0 ? "red" : "green"}>
                      {validation.metrics.schema_errors}
                    </Badge>
                  </div>
                )}
                {validation.metrics.schemas_loaded !== undefined && (
                  <div>
                    <Box variant="awsui-key-label">Schemas Loaded</Box>
                    <Box>{validation.metrics.schemas_loaded}</Box>
                  </div>
                )}
                {validation.metrics.has_calculated_data !== undefined && (
                  <div>
                    <Box variant="awsui-key-label">Calculated Data</Box>
                    <Badge color={validation.metrics.has_calculated_data ? "green" : "grey"}>
                      {validation.metrics.has_calculated_data ? "Present" : "None"}
                    </Badge>
                  </div>
                )}
                {validation.metrics.has_data_source_traceability !== undefined && (
                  <div>
                    <Box variant="awsui-key-label">Traceability</Box>
                    <Badge color={validation.metrics.has_data_source_traceability ? "green" : validation.metrics.has_calculated_data ? "red" : "grey"}>
                      {validation.metrics.has_data_source_traceability ? "Present" : validation.metrics.has_calculated_data ? "Missing" : "N/A"}
                    </Badge>
                  </div>
                )}
                {validation.metrics.unique_units !== undefined && (
                  <div>
                    <Box variant="awsui-key-label">Unique Units</Box>
                    <Box>{validation.metrics.unique_units}</Box>
                  </div>
                )}
              </ColumnLayout>
            </Container>
          )}
        </>
      )}
    </SpaceBetween>
  )
}

export default ValidateASMApp
