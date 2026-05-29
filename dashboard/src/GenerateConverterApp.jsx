// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

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
import FormField from '@cloudscape-design/components/form-field'
import Input from '@cloudscape-design/components/input'
import Select from '@cloudscape-design/components/select'

import { ENDPOINTS, authFetch } from './config'

function GenerateConverterApp() {
  const [instrumentFile, setInstrumentFile] = useState([])
  const [vendor, setVendor] = useState('')
  const [model, setModel] = useState('')
  const [instrumentType, setInstrumentType] = useState({ label: 'Solution Analyzer', value: 'solution_analyzer' })
  const [fileFormat, setFileFormat] = useState({ label: 'CSV', value: 'csv' })
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const instrumentTypeOptions = [
    { label: 'Solution Analyzer', value: 'solution_analyzer' },
    { label: 'Plate Reader', value: 'plate_reader' },
    { label: 'Cell Counter', value: 'cell_counter' },
    { label: 'Spectrophotometer', value: 'spectrophotometer' },
    { label: 'Chromatography', value: 'chromatography' },
    { label: 'qPCR', value: 'qpcr' },
    { label: 'dPCR', value: 'dpcr' },
    { label: 'Endotoxin Testing', value: 'endotoxin_testing' },
    { label: 'Electrophoresis', value: 'electrophoresis' },
    { label: 'Light Obscuration', value: 'light_obscuration' },
  ]

  const fileFormatOptions = [
    { label: 'CSV', value: 'csv' },
    { label: 'TSV', value: 'tsv' },
    { label: 'XML', value: 'xml' },
    { label: 'JSON', value: 'json' },
    { label: 'TXT', value: 'txt' },
    { label: 'XLSX', value: 'xlsx' },
  ]

  const handleGenerate = async () => {
    if (!instrumentFile.length || !vendor || !model) return

    setLoading(true)
    setProgress(10)
    setError(null)
    setResult(null)

    try {
      const fileContent = await instrumentFile[0].text()
      setProgress(20)

      const response = await authFetch(`${ENDPOINTS.ataas}/generate-converter`, {
        method: 'POST',
        body: JSON.stringify({
          file_content: fileContent,
          file_name: instrumentFile[0].name,
          manifest: {
            vendor: vendor,
            model: model,
            instrument_type: instrumentType.value,
            file_format: fileFormat.value
          },
          auto_register: true
        })
      })

      setProgress(80)

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Generation failed')
      }

      setResult(data)
      setProgress(100)

    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const downloadCode = () => {
    if (!result?.converter_code) return
    const blob = new Blob([result.converter_code], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${result.converter_id || 'converter'}.py`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="Upload a sample instrument file and let AI generate a custom converter automatically"
      >
        AI Converter Generator
      </Header>

      <Alert type="info" header="How It Works">
        <SpaceBetween size="xs">
          <div>1. Upload a sample instrument file (only headers + a few rows are sent to AI)</div>
          <div>2. Provide instrument details (vendor, model, type)</div>
          <div>3. AI analyzes the file format and generates a Python converter</div>
          <div>4. The converter is auto-registered as PENDING in the Converter Management tab</div>
          <div>5. Review the generated code, test it, then approve for production use</div>
        </SpaceBetween>
      </Alert>

      <Container header={<Header variant="h2">Step 1: Instrument Details</Header>}>
        <SpaceBetween size="m">
          <ColumnLayout columns={2}>
            <FormField label="Vendor" constraintText="Required">
              <Input
                value={vendor}
                onChange={({ detail }) => setVendor(detail.value)}
                placeholder="e.g., NOVABIO_FLEX2"
              />
            </FormField>
            <FormField label="Model" constraintText="Required">
              <Input
                value={model}
                onChange={({ detail }) => setModel(detail.value)}
                placeholder="e.g., BioProfile FLEX2"
              />
            </FormField>
          </ColumnLayout>
          <ColumnLayout columns={2}>
            <FormField label="Instrument Type">
              <Select
                selectedOption={instrumentType}
                onChange={({ detail }) => setInstrumentType(detail.selectedOption)}
                options={instrumentTypeOptions}
                filteringType="auto"
              />
            </FormField>
            <FormField label="File Format">
              <Select
                selectedOption={fileFormat}
                onChange={({ detail }) => setFileFormat(detail.selectedOption)}
                options={fileFormatOptions}
              />
            </FormField>
          </ColumnLayout>
        </SpaceBetween>
      </Container>

      <Container header={<Header variant="h2">Step 2: Upload Sample File</Header>}>
        <SpaceBetween size="m">
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
            tokenLimit={1}
            constraintText="Sample instrument output file — only headers + first few rows are sent to AI"
          />

          <Button
            variant="primary"
            onClick={handleGenerate}
            loading={loading}
            disabled={!instrumentFile.length || !vendor || !model}
          >
            Generate Converter with AI
          </Button>

          {loading && (
            <ProgressBar
              value={progress}
              label="Generating..."
              description="AI is analyzing your file and generating converter code..."
            />
          )}

          {error && (
            <Alert type="error" header="Generation Failed">{error}</Alert>
          )}
        </SpaceBetween>
      </Container>

      {result && (
        <>
          <Container header={<Header variant="h2">Step 3: Results</Header>}>
            <SpaceBetween size="m">
              <ColumnLayout columns={4} variant="text-grid">
                <div>
                  <Box variant="awsui-key-label">Converter ID</Box>
                  <Box fontWeight="bold">{result.converter_id}</Box>
                </div>
                <div>
                  <Box variant="awsui-key-label">Status</Box>
                  <Badge color={result.registration?.registered ? 'green' : 'grey'}>
                    {result.registration?.registered ? 'REGISTERED (PENDING)' : 'NOT REGISTERED'}
                  </Badge>
                </div>
                <div>
                  <Box variant="awsui-key-label">File Analysis</Box>
                  <Box>{result.file_analysis?.total_rows} rows, {result.file_analysis?.file_format} format</Box>
                </div>
                <div>
                  <Box variant="awsui-key-label">Generated By</Box>
                  <Box>Bedrock Claude 3.5 Sonnet</Box>
                </div>
              </ColumnLayout>

              {result.registration?.registered && (
                <Alert type="success" header="Converter Registered">
                  The converter has been registered as <strong>{result.converter_id}</strong> with status PENDING.
                  Go to the <strong>Converter Management</strong> tab to review the code and approve it for production use.
                </Alert>
              )}

              <SpaceBetween direction="horizontal" size="xs">
                <Button variant="primary" iconName="download" onClick={downloadCode}>
                  Download Converter Code
                </Button>
              </SpaceBetween>
            </SpaceBetween>
          </Container>

          <ExpandableSection headerText="Generated Converter Code" variant="container" defaultExpanded>
            <pre style={{
              background: '#232f3e', color: '#d5dbdb', padding: '16px',
              borderRadius: '4px', overflow: 'auto', fontSize: '12px',
              maxHeight: '500px', whiteSpace: 'pre-wrap'
            }}>
              {result.converter_code}
            </pre>
          </ExpandableSection>
        </>
      )}
    </SpaceBetween>
  )
}

export default GenerateConverterApp
