// Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
// Licensed under the Apache License, Version 2.0 (the "License").
// You may not use this file except in compliance with the License.
// A copy of the License is located at http://aws.amazon.com/apache2.0/
// This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
import { useState } from 'react'
import Container from '@cloudscape-design/components/container'
import Header from '@cloudscape-design/components/header'
import SpaceBetween from '@cloudscape-design/components/space-between'
import FormField from '@cloudscape-design/components/form-field'
import Input from '@cloudscape-design/components/input'
import Textarea from '@cloudscape-design/components/textarea'
import Button from '@cloudscape-design/components/button'
import Alert from '@cloudscape-design/components/alert'
import FileUpload from '@cloudscape-design/components/file-upload'
import StatusIndicator from '@cloudscape-design/components/status-indicator'
import Box from '@cloudscape-design/components/box'
import Select from '@cloudscape-design/components/select'

export default function ConverterRegistry() {
  const [converterFile, setConverterFile] = useState([])
  const [converterName, setConverterName] = useState('')
  const [manufacturer, setManufacturer] = useState('')
  const [model, setModel] = useState('')
  const [instrumentType, setInstrumentType] = useState(null)
  const [description, setDescription] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadStatus, setUploadStatus] = useState(null)
  const [validationErrors, setValidationErrors] = useState([])

  const instrumentTypeOptions = [
    { label: 'Solution Analyzer', value: 'solution_analyzer' },
    { label: 'Cell Counter', value: 'cell_counter' },
    { label: 'Plate Reader', value: 'plate_reader' },
    { label: 'Spectrophotometer', value: 'spectrophotometer' },
    { label: 'qPCR', value: 'qpcr' },
    { label: 'dPCR', value: 'dpcr' },
    { label: 'Chromatography', value: 'chromatography' },
    { label: 'Mass Spectrometry', value: 'mass_spectrometry' }
  ]

  const validateConverter = async (file) => {
    // Basic validation checks
    const errors = []
    
    if (!file.name.endsWith('.py')) {
      errors.push('Converter must be a Python (.py) file')
    }
    
    if (file.size > 1024 * 1024) { // 1MB limit
      errors.push('File size must be less than 1MB')
    }

    // Read file content for basic checks
    try {
      const content = await file.text()
      
      if (!content.includes('def convert')) {
        errors.push('Converter must contain a convert function')
      }
      
      if (!content.includes('import')) {
        errors.push('Converter should import required libraries')
      }

      // Check for dangerous patterns
      const dangerousPatterns = ['eval(', 'exec(', '__import__', 'os.system', 'subprocess']
      for (const pattern of dangerousPatterns) {
        if (content.includes(pattern)) {
          errors.push(`Security risk: Code contains potentially dangerous pattern: ${pattern}`)
        }
      }
    } catch (err) {
      errors.push('Unable to read file content')
    }

    return errors
  }

  const handleUpload = async () => {
    if (!converterFile.length || !converterName || !manufacturer || !model || !instrumentType) {
      setUploadStatus({ type: 'error', message: 'Please fill in all required fields' })
      return
    }

    setUploading(true)
    setValidationErrors([])

    try {
      // Validate converter code
      const errors = await validateConverter(converterFile[0])
      
      if (errors.length > 0) {
        setValidationErrors(errors)
        setUploadStatus({ 
          type: 'error', 
          message: 'Validation failed. Please fix the issues and try again.' 
        })
        setUploading(false)
        return
      }

      // Read file content
      const fileContent = await converterFile[0].text()

      // Upload to S3 via API
      const response = await fetch('/api/converters/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          converter_name: converterName,
          manufacturer: manufacturer,
          model: model,
          instrument_type: instrumentType.value,
          description: description,
          code: fileContent,
          filename: converterFile[0].name
        })
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const result = await response.json()

      setUploadStatus({ 
        type: 'success', 
        message: `Converter uploaded successfully! Approval ID: ${result.approval_id}` 
      })

      // Reset form
      setConverterFile([])
      setConverterName('')
      setManufacturer('')
      setModel('')
      setInstrumentType(null)
      setDescription('')

    } catch (error) {
      setUploadStatus({ 
        type: 'error', 
        message: `Upload failed: ${error.message}` 
      })
    } finally {
      setUploading(false)
    }
  }

  return (
    <SpaceBetween size="l">
      <Alert type="info">
        Register a custom converter for instruments not supported by the allotropy library. 
        Upload your Python converter code, and it will be reviewed and approved before deployment.
      </Alert>

      <Container header={<Header variant="h2">Converter Information</Header>}>
        <SpaceBetween size="m">
          <FormField 
            label="Converter Name" 
            description="Unique name for this converter"
            constraintText="Required"
          >
            <Input
              value={converterName}
              onChange={({ detail }) => setConverterName(detail.value)}
              placeholder="e.g., nova_flex2_converter"
            />
          </FormField>

          <FormField 
            label="Manufacturer" 
            description="Instrument manufacturer"
            constraintText="Required"
          >
            <Input
              value={manufacturer}
              onChange={({ detail }) => setManufacturer(detail.value)}
              placeholder="e.g., Nova Biomedical"
            />
          </FormField>

          <FormField 
            label="Model" 
            description="Instrument model"
            constraintText="Required"
          >
            <Input
              value={model}
              onChange={({ detail }) => setModel(detail.value)}
              placeholder="e.g., BioProfile FLEX2"
            />
          </FormField>

          <FormField 
            label="Instrument Type" 
            description="Type of instrument"
            constraintText="Required"
          >
            <Select
              selectedOption={instrumentType}
              onChange={({ detail }) => setInstrumentType(detail.selectedOption)}
              options={instrumentTypeOptions}
              placeholder="Select instrument type"
            />
          </FormField>

          <FormField 
            label="Description" 
            description="Brief description of what this converter does"
          >
            <Textarea
              value={description}
              onChange={({ detail }) => setDescription(detail.value)}
              placeholder="e.g., Converts Nova FLEX2 CSV files with blood gas, pH, osmolality, and metabolite data to ASM solution analyzer format"
              rows={3}
            />
          </FormField>
        </SpaceBetween>
      </Container>

      <Container header={<Header variant="h2">Upload Converter Code</Header>}>
        <SpaceBetween size="m">
          <Alert type="warning">
            <strong>Code Requirements:</strong>
            <ul>
              <li>Must be a Python (.py) file</li>
              <li>Must contain a convert function</li>
              <li>Must not contain dangerous patterns (eval, exec, os.system, etc.)</li>
              <li>File size limit: 1MB</li>
            </ul>
          </Alert>

          <FormField 
            label="Converter File" 
            description="Upload your Python converter code"
            constraintText="Required - .py file only"
          >
            <FileUpload
              value={converterFile}
              onChange={({ detail }) => setConverterFile(detail.value)}
              accept=".py"
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
            />
          </FormField>

          {validationErrors.length > 0 && (
            <Alert type="error" header="Validation Errors">
              <ul>
                {validationErrors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </Alert>
          )}

          {uploadStatus && (
            <Alert type={uploadStatus.type}>
              {uploadStatus.message}
            </Alert>
          )}

          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button 
                onClick={() => {
                  setConverterFile([])
                  setConverterName('')
                  setManufacturer('')
                  setModel('')
                  setInstrumentType(null)
                  setDescription('')
                  setUploadStatus(null)
                  setValidationErrors([])
                }}
              >
                Clear
              </Button>
              <Button 
                variant="primary" 
                onClick={handleUpload}
                disabled={!converterFile.length || !converterName || !manufacturer || !model || !instrumentType}
                loading={uploading}
              >
                {uploading ? 'Uploading...' : 'Upload for Approval'}
              </Button>
            </SpaceBetween>
          </Box>
        </SpaceBetween>
      </Container>

      <Container header={<Header variant="h2">What Happens Next?</Header>}>
        <SpaceBetween size="m">
          <Box>
            <StatusIndicator type="info">1. Code Validation</StatusIndicator>
            <Box margin={{ left: 'xl', top: 'xs' }}>
              Your converter code is automatically checked for security issues and basic requirements.
            </Box>
          </Box>

          <Box>
            <StatusIndicator type="info">2. Upload to S3</StatusIndicator>
            <Box margin={{ left: 'xl', top: 'xs' }}>
              If validation passes, the code is uploaded to a secure S3 bucket for review.
            </Box>
          </Box>

          <Box>
            <StatusIndicator type="info">3. Human Review</StatusIndicator>
            <Box margin={{ left: 'xl', top: 'xs' }}>
              A reviewer will examine your code offline for quality, security, and ASM compliance.
            </Box>
          </Box>

          <Box>
            <StatusIndicator type="info">4. Approval/Rejection</StatusIndicator>
            <Box margin={{ left: 'xl', top: 'xs' }}>
              The reviewer will approve or reject with comments. You can upload a new version if rejected.
            </Box>
          </Box>

          <Box>
            <StatusIndicator type="success">5. Deployment</StatusIndicator>
            <Box margin={{ left: 'xl', top: 'xs' }}>
              Once approved, the converter is deployed and available for use via the Unified Converter API.
            </Box>
          </Box>
        </SpaceBetween>
      </Container>
    </SpaceBetween>
  )
}
