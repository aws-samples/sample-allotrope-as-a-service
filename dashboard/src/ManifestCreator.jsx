import { useState } from 'react'
import Container from '@cloudscape-design/components/container'
import Header from '@cloudscape-design/components/header'
import SpaceBetween from '@cloudscape-design/components/space-between'
import FormField from '@cloudscape-design/components/form-field'
import Select from '@cloudscape-design/components/select'
import Input from '@cloudscape-design/components/input'
import Button from '@cloudscape-design/components/button'
import Box from '@cloudscape-design/components/box'
import Alert from '@cloudscape-design/components/alert'

import instrumentsData from './data/instruments.json'

export default function ManifestCreator() {
  const [selectedInstrument, setSelectedInstrument] = useState(null)
  const [isCustom, setIsCustom] = useState(false)
  const [customManufacturer, setCustomManufacturer] = useState('')
  const [customModel, setCustomModel] = useState('')
  const [customType, setCustomType] = useState({ label: 'Solution Analyzer', value: 'solution_analyzer' })
  const [serialNumber, setSerialNumber] = useState('')
  const [softwareVersion, setSoftwareVersion] = useState('')
  const [location, setLocation] = useState('')
  const [contact, setContact] = useState('')
  const [customerAlias, setCustomerAlias] = useState('')
  const [fileFormat, setFileFormat] = useState({ label: 'CSV', value: 'csv' })

  const instrumentOptions = [
    ...instrumentsData.map(inst => ({
      label: `${inst.name} (${inst.manufacturer})`,
      value: inst.canonical_id,
      description: inst.instrument_type.replace('_', ' ')
    })),
    {
      label: 'Custom Instrument (Not in Registry)',
      value: 'CUSTOM',
      description: 'AI-powered conversion'
    }
  ]

  const instrumentTypeOptions = [
    { label: 'Solution Analyzer', value: 'solution_analyzer' },
    { label: 'Cell Counter', value: 'cell_counter' },
    { label: 'Plate Reader', value: 'plate_reader' },
    { label: 'Spectrophotometer', value: 'spectrophotometer' },
    { label: 'qPCR', value: 'qpcr' },
    { label: 'dPCR', value: 'dpcr' }
  ]

  const fileFormatOptions = [
    { label: 'CSV', value: 'csv' },
    { label: 'TSV', value: 'tsv' },
    { label: 'XML', value: 'xml' },
    { label: 'JSON', value: 'json' },
    { label: 'XLSX', value: 'xlsx' }
  ]

  const handleInstrumentSelect = (option) => {
    console.log('Selected:', option)
    setSelectedInstrument(option)
    const custom = option.value === 'CUSTOM'
    console.log('Is custom:', custom)
    setIsCustom(custom)
  }

  const instrument = selectedInstrument && !isCustom
    ? instrumentsData.find(i => i.canonical_id === selectedInstrument.value)
    : null

  const manifest = selectedInstrument ? {
    vendor: isCustom ? 'CUSTOM' : instrument.vendor_id,
    instrument_type: isCustom ? customType.value : instrument.instrument_type,
    manufacturer: isCustom ? customManufacturer : instrument.manufacturer,
    model: isCustom ? customModel : instrument.name,
    file_format: fileFormat.value,
    ...(serialNumber && { serial_number: serialNumber }),
    ...(softwareVersion && { software_version: softwareVersion }),
    ...(location && { location: location }),
    ...(contact && { contact: contact }),
    ...(customerAlias && { customer_alias: customerAlias })
  } : null

  const downloadManifest = () => {
    const filename = isCustom 
      ? 'custom_instrument_manifest.json'
      : `${instrument.canonical_id}_manifest.json`
    const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  console.log('Rendering - isCustom:', isCustom, 'selectedInstrument:', selectedInstrument)

  return (
    <SpaceBetween size="l">
      <Alert type="info">
        Create a manifest file for your instrument. This file contains metadata that ensures 100% accurate ASM conversion.
        Create once per instrument, reuse for all files from that instrument.
      </Alert>

      <Container header={<Header variant="h2">Select Instrument</Header>}>
        <FormField
          label="Instrument"
          description="Search and select your instrument from the registry, or choose Custom for unlisted instruments"
        >
          <Select
            selectedOption={selectedInstrument}
            onChange={({ detail }) => handleInstrumentSelect(detail.selectedOption)}
            options={instrumentOptions}
            placeholder="Search instruments..."
            filteringType="auto"
            empty="No instruments found"
          />
        </FormField>
      </Container>

      {isCustom && (
        <Container header={<Header variant="h2">Custom Instrument Details</Header>}>
          <SpaceBetween size="m">
            <Alert key="custom-alert" type="info">
              This instrument is not in our registry. Our AI will analyze your file and generate a converter automatically.
            </Alert>

            <FormField key="custom-type" label="Instrument Type" description="Type of instrument">
              <Select
                selectedOption={customType}
                onChange={({ detail }) => setCustomType(detail.selectedOption)}
                options={instrumentTypeOptions}
              />
            </FormField>

            <FormField 
              key="custom-manufacturer"
              label="Manufacturer" 
              description="Instrument manufacturer name"
            >
              <Input
                value={customManufacturer}
                onChange={({ detail }) => setCustomManufacturer(detail.value)}
                placeholder="e.g., Acme Instruments"
              />
            </FormField>

            <FormField 
              key="custom-model"
              label="Model" 
              description="Instrument model name"
            >
              <Input
                value={customModel}
                onChange={({ detail }) => setCustomModel(detail.value)}
                placeholder="e.g., CustomAnalyzer 3000"
              />
            </FormField>
          </SpaceBetween>
        </Container>
      )}

      {instrument && !isCustom && (
        <Container header={<Header variant="h2">Instrument Details (Auto-filled)</Header>}>
          <SpaceBetween size="m">
            <Box key="vendor">
              <Box variant="awsui-key-label">Vendor ID</Box>
              <Box>{instrument.vendor_id}</Box>
            </Box>
            <Box key="manufacturer">
              <Box variant="awsui-key-label">Manufacturer</Box>
              <Box>{instrument.manufacturer}</Box>
            </Box>
            <Box key="model">
              <Box variant="awsui-key-label">Model</Box>
              <Box>{instrument.name}</Box>
            </Box>
            <Box key="type">
              <Box variant="awsui-key-label">Type</Box>
              <Box>{instrument.instrument_type.replace('_', ' ')}</Box>
            </Box>
            <Box key="allotropy">
              <Box variant="awsui-key-label">Allotropy Support</Box>
              <Box>{instrument.allotropy_supported ? '✓ Available' : '✗ Not Available'}</Box>
            </Box>
          </SpaceBetween>
        </Container>
      )}

      {(instrument || (isCustom && customManufacturer && customModel)) && (
        <>
          <Container header={<Header variant="h2">Your Instrument Details</Header>}>
            <SpaceBetween size="m">
              <FormField key="file-format" label="File Format" description="Format of your data files">
                <Select
                  selectedOption={fileFormat}
                  onChange={({ detail }) => setFileFormat(detail.selectedOption)}
                  options={fileFormatOptions}
                />
              </FormField>

              <FormField 
                key="serial-number"
                label="Serial Number (Optional)" 
                description="Your instrument's serial number for traceability"
              >
                <Input
                  value={serialNumber}
                  onChange={({ detail }) => setSerialNumber(detail.value)}
                  placeholder="e.g., FLEX2-2023-001"
                />
              </FormField>

              <FormField 
                key="software-version"
                label="Software Version (Optional)" 
                description="Instrument software version"
              >
                <Input
                  value={softwareVersion}
                  onChange={({ detail }) => setSoftwareVersion(detail.value)}
                  placeholder="e.g., v6.2.1"
                />
              </FormField>

              <FormField 
                key="location"
                label="Location (Optional)" 
                description="Where this instrument is located"
              >
                <Input
                  value={location}
                  onChange={({ detail }) => setLocation(detail.value)}
                  placeholder="e.g., Building 3, Lab 2A"
                />
              </FormField>

              <FormField 
                key="contact"
                label="Contact (Optional)" 
                description="Responsible person or team"
              >
                <Input
                  value={contact}
                  onChange={({ detail }) => setContact(detail.value)}
                  placeholder="e.g., lab.manager@company.com"
                />
              </FormField>

              <FormField 
                key="customer-alias"
                label="Your Alias (Optional)" 
                description="What you call this instrument in your lab"
              >
                <Input
                  value={customerAlias}
                  onChange={({ detail }) => setCustomerAlias(detail.value)}
                  placeholder="e.g., Lab 3 FLEX2"
                />
              </FormField>
            </SpaceBetween>
          </Container>

          <Container header={<Header variant="h2">Manifest Preview</Header>}>
            <SpaceBetween size="m">
              {isCustom && (
                <Alert key="preview-alert" type="warning">
                  Custom instrument will use AI-powered conversion. For best results, ensure your file is in a simple CSV or JSON format.
                </Alert>
              )}
              <Box key="preview-json">
                <pre style={{ 
                  background: '#f4f4f4', 
                  padding: '16px', 
                  borderRadius: '4px',
                  overflow: 'auto',
                  fontSize: '14px'
                }}>
                  {JSON.stringify(manifest, null, 2)}
                </pre>
              </Box>
              <Button key="download-button" variant="primary" onClick={downloadManifest}>
                Download manifest.json
              </Button>
            </SpaceBetween>
          </Container>
        </>
      )}
    </SpaceBetween>
  )
}
