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
import Table from '@cloudscape-design/components/table'
import StatusIndicator from '@cloudscape-design/components/status-indicator'

import { ENDPOINTS } from './config'

function ConvertInstrumentApp() {
  const [instrumentFile, setInstrumentFile] = useState([])
  const [configFile, setConfigFile] = useState([])
  const [configValidation, setConfigValidation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [asmOutput, setAsmOutput] = useState(null)
  const [validation, setValidation] = useState(null)
  const [error, setError] = useState(null)
  const [integrityReport, setIntegrityReport] = useState(null)
  const [fieldMapping, setFieldMapping] = useState(null)

  const validateConfig = (config) => {
    const errors = []
    const warnings = []
    
    // Required fields
    if (!config.vendor) {
      errors.push('Missing required field: "vendor"')
    }
    if (!config.instrument_type) {
      errors.push('Missing required field: "instrument_type"')
    }
    if (!config.manufacturer) {
      errors.push('Missing required field: "manufacturer"')
    }
    if (!config.model) {
      errors.push('Missing required field: "model"')
    }
    if (!config.file_format) {
      errors.push('Missing required field: "file_format"')
    }
    
    // Recommended fields for regulatory compliance
    if (!config.serial_number) {
      warnings.push('Missing recommended field: "serial_number" (needed for full regulatory compliance)')
    }
    if (!config.software_version) {
      warnings.push('Missing recommended field: "software_version" (needed for full regulatory compliance)')
    }
    
    // Valid instrument types
    const validTypes = [
      'solution_analyzer', 'cell_counter', 'plate_reader', 
      'spectrophotometer', 'qpcr', 'dpcr', 'chromatography',
      'endotoxin_testing', 'electrophoresis', 'light_obscuration'
    ]
    if (config.instrument_type && !validTypes.includes(config.instrument_type)) {
      warnings.push(`Instrument type "${config.instrument_type}" may not be recognized. Valid types: ${validTypes.join(', ')}`)
    }
    
    // Valid file formats
    const validFormats = ['csv', 'tsv', 'xml', 'json', 'xlsx', 'txt', 'xls', 'dat', 'raw', 'bin', 'asc']
    if (config.file_format && !validFormats.includes(config.file_format.toLowerCase())) {
      warnings.push(`File format "${config.file_format}" is not a common format. Ensure your custom converter supports it.`)
    }
    
    return { errors, warnings }
  }

  const handleConfigFileChange = async (files) => {
    setConfigFile(files)
    setConfigValidation(null)
    
    if (files.length === 0) return
    
    try {
      const content = await files[0].text()
      const config = JSON.parse(content)
      const validation = validateConfig(config)
      setConfigValidation(validation)
    } catch (err) {
      setConfigValidation({
        errors: [`Invalid JSON file: ${err.message}`],
        warnings: []
      })
    }
  }

  const handleConvert = async () => {
    if (!instrumentFile.length || !configFile.length) return
    
    setLoading(true)
    setProgress(10)
    setError(null)
    setAsmOutput(null)
    setValidation(null)

    try {
      // Read files
      const fileContent = await instrumentFile[0].text()
      const configContent = await configFile[0].text()
      setProgress(20)
      
      // Parse config file
      let config
      try {
        config = JSON.parse(configContent)
      } catch (parseError) {
        throw new Error(`Invalid JSON in instrument config file: ${parseError.message}`)
      }
      
      // Validate config file structure
      const validation = validateConfig(config)
      if (validation.errors.length > 0) {
        const errorList = validation.errors.map((e, i) => `${i + 1}. ${e}`).join('\n')
        throw new Error(`Instrument config file has errors:\n\n${errorList}\n\nPlease fix these issues and try again. You can create a valid config file using the "Instrument Config Creator" tab.`)
      }
      
      // Show warnings if any (but continue)
      if (validation.warnings.length > 0) {
        console.warn('Config file warnings:', validation.warnings)
      }
      
      // Step 1: Convert instrument file to ASM
      const convertResponse = await fetch(`${ENDPOINTS.unifiedConverter}/convert`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_content: fileContent,
          file_name: instrumentFile[0].name,
          manifest: config,
          store_results: true
        })
      })
      
      const contentType = convertResponse.headers.get('content-type')
      if (!contentType || !contentType.includes('application/json')) {
        const text = await convertResponse.text()
        console.error('Non-JSON response:', text.substring(0, 200))
        throw new Error('API returned non-JSON response. Check CORS or endpoint.')
      }
      
      const convertResult = await convertResponse.json()
      
      if (!convertResponse.ok) {
        throw new Error(convertResult.error || 'Conversion failed')
      }
      
      // Handle both asm and asm_output field names
      const asmData = convertResult.asm || convertResult.asm_output
      
      if (!asmData) {
        throw new Error('No ASM data returned from conversion')
      }
      
      setAsmOutput(asmData)
      setFieldMapping(convertResult.field_mapping || null)
      setProgress(60)

      // Step 2: Validate the generated ASM
      const validateResponse = await fetch(`${ENDPOINTS.dvaas}/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          asm_data: asmData,
          validation_level: 'comprehensive',
          use_allotropy_validator: true,
          generate_report: true,
          file_name: instrumentFile[0].name.replace(/\.[^/.]+$/, '') + '_asm.json'
        })
      })
      
      const validateResult = await validateResponse.json()
      
      if (!validateResponse.ok) {
        throw new Error(validateResult.error || 'Validation failed')
      }
      
      setValidation(validateResult)
      
      // Step 3: Data Integrity Verification (from converter's field mapping)
      if (convertResult.field_mapping && convertResult.field_mapping.length > 0) {
        const comparisons = convertResult.field_mapping.map(m => ({
          field: m.source_field,
          sourceRow: m.source_row || m.row,
          sourceValue: String(m.source_value),
          asmValue: String(m.asm_value),
          asmField: m.asm_path || m.asm_field,
          unit: m.unit || '',
          match: String(m.source_value) == String(m.asm_value) || parseFloat(m.source_value) === parseFloat(m.asm_value)
        }))
        setIntegrityReport({
          comparisons,
          supported: true,
          summary: convertResult.integrity_summary || null
        })
      } else {
        setIntegrityReport(null)
      }
      setProgress(100)

    } catch (err) {
      console.error('Error:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const downloadASM = () => {
    if (!asmOutput) return
    
    const blob = new Blob([JSON.stringify(asmOutput, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = instrumentFile[0].name.replace(/\.[^/.]+$/, '') + '_asm.json'
    a.click()
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
    a.download = `validation_report_${instrumentFile[0]?.name || 'asm'}.pdf`
    a.click()
  }

  const getRecommendations = (errors, warnings) => {
    const recommendations = []
    
    if (errors?.some(e => e.includes('data-source-aggregate-document') || e.includes('traceability'))) {
      recommendations.push({
        issue: 'Missing Data Source Traceability',
        severity: 'high',
        description: 'Calculated values are not linked to their source measurements.',
        fix: 'The converter needs to add traceability links. This is a converter issue, not a data issue.'
      })
    }
    
    if (errors?.some(e => e.includes('measurement') && e.includes('not found'))) {
      recommendations.push({
        issue: 'Missing Measurement Documents',
        severity: 'high',
        description: 'The converter did not generate proper measurement documents.',
        fix: 'Check your instrument config file to ensure vendor and model are correct.'
      })
    }
    
    if (warnings?.some(w => w.includes('unit') || w.includes('Unit'))) {
      recommendations.push({
        issue: 'Unknown or Non-Standard Units',
        severity: 'medium',
        description: 'Some measurement units are not recognized by the Allotrope standard.',
        fix: 'This is expected for some instruments. The data is still valid and usable.'
      })
    }
    
    if (warnings?.some(w => w.includes('serial') || w.includes('software'))) {
      recommendations.push({
        issue: 'Missing Equipment Metadata',
        severity: 'low',
        description: 'Equipment serial number or software version is missing.',
        fix: 'Add serial_number and software_version to your instrument config file for full regulatory compliance.'
      })
    }
    
    return recommendations
  }

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="Convert instrument files to ASM format with automatic validation"
      >
        Convert Instrument File
      </Header>

      {/* File Uploads */}
      <Container header={<Header variant="h2">Step 1: Upload Files</Header>}>
        <SpaceBetween size="m">
          <div>
            <Box variant="h3" padding={{ bottom: 's' }}>Instrument File</Box>
            <FileUpload
              onChange={({ detail }) => setInstrumentFile(detail.value)}
              value={instrumentFile}
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
              constraintText="Raw instrument output file"
            />
          </div>

          <div>
            <Box variant="h3" padding={{ bottom: 's' }}>Instrument Config</Box>
            <FileUpload
              onChange={({ detail }) => handleConfigFileChange(detail.value)}
              value={configFile}
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
              constraintText="Instrument configuration file (JSON) - previously called manifest.json"
              accept=".json"
            />
          </div>
          
          <Alert type="info" header="What is an Instrument Config?">
            The instrument config file (previously called manifest.json) contains metadata about your instrument:
            vendor, model, instrument type, serial number, etc. You can create one using the "Instrument Config Creator" tab.
          </Alert>
          
          {configValidation && (
            <>
              {configValidation.errors.length > 0 && (
                <Alert type="error" header="Config File Has Errors">
                  <SpaceBetween size="xs">
                    {configValidation.errors.map((err, i) => (
                      <div key={i}>• {err}</div>
                    ))}
                    <div style={{ marginTop: '8px' }}>
                      <strong>Fix these errors before converting.</strong> Use the "Instrument Config Creator" tab to generate a valid config file.
                    </div>
                  </SpaceBetween>
                </Alert>
              )}
              
              {configValidation.errors.length === 0 && configValidation.warnings.length > 0 && (
                <Alert type="warning" header="Config File Has Warnings">
                  <SpaceBetween size="xs">
                    {configValidation.warnings.map((warn, i) => (
                      <div key={i}>• {warn}</div>
                    ))}
                    <div style={{ marginTop: '8px' }}>
                      You can proceed with conversion, but adding these fields is recommended for full regulatory compliance.
                    </div>
                  </SpaceBetween>
                </Alert>
              )}
              
              {configValidation.errors.length === 0 && configValidation.warnings.length === 0 && (
                <Alert type="success" header="Config File is Valid">
                  Your instrument config file has all required fields and is ready for conversion.
                </Alert>
              )}
            </>
          )}
        </SpaceBetween>
      </Container>

      {/* Action Button */}
      <Container header={<Header variant="h2">Step 2: Convert & Validate</Header>}>
        <SpaceBetween size="m">
          <Button
            variant="primary"
            onClick={handleConvert}
            loading={loading}
            disabled={!instrumentFile.length || !configFile.length || (configValidation?.errors?.length > 0)}
          >
            Convert to ASM & Validate
          </Button>

          {loading && (
            <ProgressBar
              value={progress}
              label="Processing..."
              description="Converting instrument file to ASM and validating..."
            />
          )}

          {error && (
            <Alert type="error" header="Error">
              {error}
            </Alert>
          )}
        </SpaceBetween>
      </Container>

      {/* Conversion Results */}
      {asmOutput && validation && (
        <>
          <Container header={<Header variant="h2">Step 3: Conversion Results</Header>}>
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
                  <Box>{validation.validator || 'DVaaS'}</Box>
                </div>
              </ColumnLayout>

              {validation.valid ? (
                <Alert type="success" header="Conversion Successful">
                  Your instrument file has been successfully converted to ASM format and validated. 
                  The ASM file is ready for use and meets Allotrope standards.
                </Alert>
              ) : (
                <Alert type="warning" header="Conversion Complete with Issues">
                  Your instrument file has been converted to ASM format, but the validation found {validation.errors?.length || 0} error(s) 
                  and {validation.warnings?.length || 0} warning(s). Review the details below.
                </Alert>
              )}

              <SpaceBetween size="s" direction="horizontal">
                <Button
                  variant="primary"
                  iconName="download"
                  onClick={downloadASM}
                >
                  Download ASM File
                </Button>
                
                {validation.certification_report?.available && (
                  <Button
                    iconName="download"
                    onClick={downloadPDF}
                  >
                    Download Validation Report (PDF)
                  </Button>
                )}
              </SpaceBetween>
            </SpaceBetween>
          </Container>

          {/* Errors */}
          {validation.errors?.length > 0 && (
            <Container header={<Header variant="h2" description="Critical issues found during validation">Errors ({validation.errors.length})</Header>}>
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
          {(validation.errors?.length > 0 || validation.warnings?.length > 0) && getRecommendations(validation.errors, validation.warnings).length > 0 && (
            <Container header={<Header variant="h2" description="Suggestions for addressing validation issues">Recommendations</Header>}>
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
                    </SpaceBetween>
                  </ExpandableSection>
                ))}
              </SpaceBetween>
            </Container>
          )}

          {/* Data Integrity Verification */}
          {integrityReport && integrityReport.supported && integrityReport.comparisons.length > 0 && (
            <Container header={
              <Header variant="h2" 
                description="Proof that source values are preserved exactly in the ASM output"
                counter={`(${integrityReport.comparisons.filter(c => c.match).length}/${integrityReport.comparisons.length} matched)`}
              >
                Data Integrity Verification
              </Header>
            }>
              <SpaceBetween size="m">
                {integrityReport.summary && (
                  <ColumnLayout columns={4} variant="text-grid">
                    <div>
                      <Box variant="awsui-key-label">Coverage</Box>
                      <Box fontSize="heading-xl">{integrityReport.summary.coverage_pct}%</Box>
                    </div>
                    <div>
                      <Box variant="awsui-key-label">Mapped Values</Box>
                      <Box fontSize="heading-xl">{integrityReport.summary.mapped_to_source}</Box>
                    </div>
                    <div>
                      <Box variant="awsui-key-label">Source Cells</Box>
                      <Box>{integrityReport.summary.unique_source_cells}</Box>
                    </div>
                    <div>
                      <Box variant="awsui-key-label">Source Rows</Box>
                      <Box>{integrityReport.summary.source_rows}</Box>
                    </div>
                  </ColumnLayout>
                )}

                {integrityReport.comparisons.every(c => c.match) ? (
                  <Alert type="success" header="Data Integrity Confirmed">
                    All mapped source values were preserved exactly in the ASM output. No values were altered, rounded, or lost during conversion.
                  </Alert>
                ) : (
                  <Alert type="info" header="Data Integrity Report">
                    {integrityReport.comparisons.filter(c => c.match).length} of {integrityReport.comparisons.length} values matched exactly.
                    Differences may be due to type formatting (e.g. "1.80" → 1.8).
                  </Alert>
                )}

                <Table
                  columnDefinitions={[
                    {
                      id: 'field',
                      header: 'Source Field',
                      cell: item => <Box fontWeight="bold">{item.field}</Box>
                    },
                    {
                      id: 'row',
                      header: 'Row',
                      cell: item => item.sourceRow
                    },
                    {
                      id: 'source',
                      header: 'Source Value',
                      cell: item => item.sourceValue
                    },
                    {
                      id: 'asmField',
                      header: 'ASM Path',
                      cell: item => {
                        const parts = (item.asmField || '').split('/')
                        return parts.slice(-2).join('/')
                      }
                    },
                    {
                      id: 'asm',
                      header: 'ASM Value',
                      cell: item => item.asmValue
                    },
                    {
                      id: 'unit',
                      header: 'Unit',
                      cell: item => item.unit
                    },
                    {
                      id: 'status',
                      header: 'Match',
                      cell: item => item.match 
                        ? <StatusIndicator type="success">Match</StatusIndicator>
                        : <StatusIndicator type="warning">Formatted</StatusIndicator>
                    }
                  ]}
                  items={integrityReport.comparisons.slice(0, 50)}
                  variant="embedded"
                  footer={integrityReport.comparisons.length > 50 
                    ? <Box textAlign="center" color="text-body-secondary">Showing first 50 of {integrityReport.comparisons.length} mappings</Box>
                    : null
                  }
                />
              </SpaceBetween>
            </Container>
          )}

          {/* File Metrics */}
          {validation.metrics && (
            <Container header={<Header variant="h2">ASM File Metrics</Header>}>
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
              </ColumnLayout>
            </Container>
          )}
        </>
      )}
    </SpaceBetween>
  )
}

export default ConvertInstrumentApp
