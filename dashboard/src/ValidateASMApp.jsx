import { useState } from 'react'
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

// Service endpoint
const VALIDATE_ENDPOINT = 'https://4ndgjn16zd.execute-api.us-east-1.amazonaws.com/prod/validate'

function ValidateASMApp() {
  const [file, setFile] = useState([])
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [validation, setValidation] = useState(null)
  const [error, setError] = useState(null)

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
      setProgress(50)

      // Validate ASM
      const response = await fetch(VALIDATE_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asm_data: asmData,
          validation_level: 'comprehensive',
          use_allotropy_validator: true,
          generate_report: true,
          file_name: file[0].name
        })
      })
      
      const result = await response.json()
      console.log('Validation result:', result)
      
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

  const getRecommendations = (errors, warnings) => {
    const recommendations = []
    
    // Analyze errors and provide recommendations
    if (errors?.some(e => e.includes('data-source-aggregate-document') || e.includes('traceability'))) {
      recommendations.push({
        issue: 'Missing Data Source Traceability',
        severity: 'high',
        description: 'Calculated values are not linked to their source measurements.',
        fix: 'Add a "data source aggregate document" inside each calculated data document that references the measurement identifiers used in the calculation.',
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
    
    if (errors?.some(e => e.includes('measurement') && e.includes('not found'))) {
      recommendations.push({
        issue: 'Missing Measurement Documents',
        severity: 'high',
        description: 'The ASM file structure is missing required measurement documents.',
        fix: 'Ensure your ASM file follows the proper nested structure with measurement aggregate document containing measurement documents.',
        example: `"measurement aggregate document": {
  "measurement document": [{
    "measurement identifier": "measurement-1",
    "device type": "pH meter",
    "pH": {"value": 7.183, "unit": "pH"}
  }]
}`
      })
    }
    
    if (errors?.some(e => e.includes('manifest'))) {
      recommendations.push({
        issue: 'Invalid or Missing Manifest',
        severity: 'high',
        description: 'The $asm.manifest field is missing or points to an invalid schema.',
        fix: 'Add a valid Allotrope manifest URL that matches your instrument type.',
        example: `"$asm.manifest": "http://purl.allotrope.org/manifests/solution-analyzer/REC/2025/06/solution-analyzer.manifest"`
      })
    }
    
    if (warnings?.some(w => w.includes('unit') || w.includes('Unit'))) {
      recommendations.push({
        issue: 'Unknown or Non-Standard Units',
        severity: 'medium',
        description: 'Some measurement units are not recognized by the Allotrope standard.',
        fix: 'Use standard SI units or Allotrope-approved unit codes. Common units: pH, mmHg, mmol/L, g/L, mOsm/kg.',
        example: `"pH": {"value": 7.183, "unit": "pH"}
"pO2": {"value": 94.5, "unit": "mmHg"}
"glucose": {"value": 2.5, "unit": "g/L"}`
      })
    }
    
    if (warnings?.some(w => w.includes('serial') || w.includes('software'))) {
      recommendations.push({
        issue: 'Missing Equipment Metadata',
        severity: 'low',
        description: 'Equipment serial number or software version is missing.',
        fix: 'Add device serial number and software version to the device system document for full regulatory compliance.',
        example: `"device system document": {
  "device identifier": "FLEX2-2023-001",
  "equipment serial number": "FLEX2-2023-001",
  "firmware version": "6.2.1"
}`
      })
    }
    
    // If no specific recommendations, provide general guidance
    if (recommendations.length === 0 && (errors?.length > 0 || warnings?.length > 0)) {
      recommendations.push({
        issue: 'General ASM Compliance Issues',
        severity: 'medium',
        description: 'Your ASM file has validation issues that need attention.',
        fix: 'Review the errors and warnings below. Ensure your ASM file follows the Allotrope Simple Model schema for your instrument type.',
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
                  <Box variant="awsui-key-label">Status</Box>
                  <Badge color={validation.valid ? "green" : "red"} size="large">
                    {validation.valid ? "VALID" : "INVALID"}
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
                  <Box>DVaaS</Box>
                </div>
              </ColumnLayout>

              {validation.valid ? (
                <Alert type="success" header="ASM File is Valid">
                  Your ASM file meets Allotrope standards and is ready for use. You can download the validation report below.
                </Alert>
              ) : (
                <Alert type="error" header="ASM File Has Issues">
                  Your ASM file has {validation.errors?.length || 0} error(s) and {validation.warnings?.length || 0} warning(s). 
                  Please review the details below and fix the issues.
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
            <Container header={<Header variant="h2" description="Issues that should be addressed for full compliance">Warnings ({validation.warnings.length})</Header>}>
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
                      
                      {rec.example && (
                        <div>
                          <Box variant="awsui-key-label">Example</Box>
                          <Box variant="code">
                            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                              {rec.example}
                            </pre>
                          </Box>
                        </div>
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
                {validation.metrics.technique && (
                  <div>
                    <Box variant="awsui-key-label">Technique</Box>
                    <Box>{validation.metrics.technique}</Box>
                  </div>
                )}
                {validation.metrics.technique_confidence && (
                  <div>
                    <Box variant="awsui-key-label">Confidence</Box>
                    <Box>{validation.metrics.technique_confidence}%</Box>
                  </div>
                )}
                {validation.metrics.measurement_count !== undefined && (
                  <div>
                    <Box variant="awsui-key-label">Measurements</Box>
                    <Box>{validation.metrics.measurement_count}</Box>
                  </div>
                )}
                {validation.metrics.has_sample_document !== undefined && (
                  <div>
                    <Box variant="awsui-key-label">Sample Document</Box>
                    <Badge color={validation.metrics.has_sample_document ? "green" : "red"}>
                      {validation.metrics.has_sample_document ? "Present" : "Missing"}
                    </Badge>
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
