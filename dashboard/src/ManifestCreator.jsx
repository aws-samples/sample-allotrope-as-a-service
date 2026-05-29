// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

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

import { ENDPOINTS, authFetch } from './config'
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
  const [uncPath, setUncPath] = useState('')
  const [timezone, setTimezone] = useState('')
  const [dateFormat, setDateFormat] = useState(null)
  const [contact, setContact] = useState('')
  const [customerAlias, setCustomerAlias] = useState('')
  const [fileFormat, setFileFormat] = useState({ label: 'CSV', value: 'csv' })
  const [converterId, setConverterId] = useState('')
  const [availableConverters, setAvailableConverters] = useState([])

  const [allInstrumentOptions, setAllInstrumentOptions] = useState([
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
  ])

  // Fetch registered converters and add to dropdown
  useState(() => {
    const fetchRegistered = async () => {
      try {
        const resp = await authFetch(`${ENDPOINTS.customConverter}/list`)
        const data = await resp.json()
        const registered = (data.converters || []).filter(c => c.status === 'APPROVED')
        const staticIds = new Set(instrumentsData.map(i => i.vendor_id))
        const newOptions = registered
          .filter(c => !staticIds.has(c.vendor))
          .map(c => ({
            label: `${c.model || c.converter_id} (${c.vendor})`,
            value: `registered-${c.converter_id}`,
            description: `${(c.instrument_type || '').replace('_', ' ')} — converter: ${c.converter_id}`
          }))
        if (newOptions.length > 0) {
          setAllInstrumentOptions(prev => [
            ...prev.filter(o => o.value !== 'CUSTOM'),
            ...newOptions,
            { label: 'Custom Instrument (Not in Registry)', value: 'CUSTOM', description: 'AI-powered conversion' }
          ])
        }
      } catch (e) { /* ignore */ }
    }
    fetchRegistered()
  })

  const instrumentTypeOptions = [
    { label: 'Solution Analyzer', value: 'solution_analyzer' },
    { label: 'Cell Counter', value: 'cell_counter' },
    { label: 'Plate Reader', value: 'plate_reader' },
    { label: 'Spectrophotometer', value: 'spectrophotometer' },
    { label: 'qPCR', value: 'qpcr' },
    { label: 'dPCR', value: 'dpcr' },
    { label: 'Chromatography', value: 'chromatography' },
    { label: 'Endotoxin Testing', value: 'endotoxin_testing' },
    { label: 'Electrophoresis', value: 'electrophoresis' },
    { label: 'Light Obscuration', value: 'light_obscuration' }
  ]

  const fileFormatOptions = [
    { label: 'CSV', value: 'csv' },
    { label: 'TSV', value: 'tsv' },
    { label: 'XML', value: 'xml' },
    { label: 'JSON', value: 'json' },
    { label: 'XLSX', value: 'xlsx' },
    { label: 'XLS', value: 'xls' },
    { label: 'TXT', value: 'txt' },
    { label: 'DAT', value: 'dat' },
    { label: 'ASC', value: 'asc' }
  ]

  const handleInstrumentSelect = (option) => {
    setSelectedInstrument(option)
    const custom = option.value === 'CUSTOM'
    const isRegistered = option.value.startsWith('registered-')
    setIsCustom(custom)
    setConverterId('')

    if (isRegistered) {
      // Extract converter_id and pre-fill from API data
      const cId = option.value.replace('registered-', '')
      setConverterId(cId)
      // Fetch converter details to populate fields
      authFetch(`${ENDPOINTS.customConverter}/list`)
        .then(r => r.json())
        .then(data => {
          const conv = (data.converters || []).find(c => c.converter_id === cId)
          if (conv) {
            setCustomManufacturer(conv.vendor || '')
            setCustomModel(conv.model || '')
            setAvailableConverters([conv])
          }
        })
        .catch(() => {})
    } else if (!custom) {
      const inst = instrumentsData.find(i => i.canonical_id === option.value)
      if (inst) fetchConverters(inst.vendor_id, inst.name)
    }
  }

  const fetchConverters = async (vendor, model) => {
    try {
      const resp = await authFetch(`${ENDPOINTS.customConverter}/list`)
      const data = await resp.json()
      const matching = (data.converters || []).filter(c =>
        c.status === 'APPROVED' && (c.vendor === vendor || c.model === model)
      )
      setAvailableConverters(matching)
    } catch (e) {
      setAvailableConverters([])
    }
  }

  const instrument = selectedInstrument && !isCustom && !selectedInstrument.value.startsWith('registered-')
    ? instrumentsData.find(i => i.canonical_id === selectedInstrument.value)
    : null

  const isRegistered = selectedInstrument && selectedInstrument.value.startsWith('registered-')

  const manifest = selectedInstrument ? {
    vendor: isCustom ? 'CUSTOM' : isRegistered ? customManufacturer : instrument.vendor_id,
    instrument_type: isCustom ? customType.value : isRegistered ? customType.value : instrument.instrument_type,
    manufacturer: isCustom ? customManufacturer : isRegistered ? customManufacturer : instrument.manufacturer,
    model: isCustom ? customModel : isRegistered ? customModel : instrument.name,
    file_format: fileFormat.value,
    ...(serialNumber && { serial_number: serialNumber }),
    ...(softwareVersion && { software_version: softwareVersion }),
    ...((location || uncPath || timezone || dateFormat) && { location: {
      ...(location && { description: location }),
      ...(uncPath && { unc_path: uncPath }),
      ...(timezone && { timezone: timezone }),
      ...(dateFormat && { date_format: dateFormat.value })
    }}),
    ...(contact && { contact: contact }),
    ...(customerAlias && { customer_alias: customerAlias }),
    ...(converterId && { converter_id: converterId })
  } : null

  const downloadManifest = () => {
    const filename = isCustom 
      ? 'custom_instrument_config.json'
      : `${instrument.canonical_id}_config.json`
    const blob = new Blob([JSON.stringify(manifest, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }


  return (
    <SpaceBetween size="l">
      <Alert type="info">
        Create an instrument config file for your instrument. This file contains metadata that ensures 100% accurate ASM conversion.
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
            options={allInstrumentOptions}
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

      {(instrument || isCustom || (selectedInstrument && selectedInstrument.value.startsWith('registered-'))) && (
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
                key="unc-path"
                label="Source File Path (Optional)" 
                description="Mount path or UNC path where instrument writes output files. Used for traceability back to the original source."
              >
                <Input
                  value={uncPath}
                  onChange={({ detail }) => setUncPath(detail.value)}
                  placeholder="e.g., /mnt/America/New_York/Nova_Biomedical_BioProfile_Flex2/MERCK_SERVER1/ExportDEV/Results"
                />
              </FormField>

              <FormField 
                key="timezone"
                label="Timezone (Optional)" 
                description="IANA timezone of the instrument location. Used to correctly interpret timestamps in the source file."
              >
                <Input
                  value={timezone}
                  onChange={({ detail }) => setTimezone(detail.value)}
                  placeholder="e.g., America/New_York"
                />
              </FormField>

              <FormField 
                key="date-format"
                label="Date Format (Optional)" 
                description="How dates appear in the instrument output file. Critical for multi-site deployments where US and European formats differ."
              >
                <Select
                  selectedOption={dateFormat}
                  onChange={({ detail }) => setDateFormat(detail.selectedOption)}
                  options={[
                    { label: 'MM/DD/YYYY (US)', value: 'MM/DD/YYYY' },
                    { label: 'DD/MM/YYYY (Europe)', value: 'DD/MM/YYYY' },
                    { label: 'YYYY-MM-DD (ISO 8601)', value: 'YYYY-MM-DD' },
                    { label: 'DD.MM.YYYY (Germany)', value: 'DD.MM.YYYY' },
                    { label: 'YYYY/MM/DD (Japan)', value: 'YYYY/MM/DD' },
                  ]}
                  placeholder="Select date format"
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

              {availableConverters.length > 0 && (
                <FormField 
                  key="converter-id"
                  label="Preferred Converter (Optional)" 
                  description="Select a specific converter for this instrument. If not set, the system auto-selects the best available converter."
                >
                  <Select
                    selectedOption={converterId ? { label: converterId, value: converterId } : null}
                    onChange={({ detail }) => setConverterId(detail.selectedOption?.value || '')}
                    options={[
                      { label: 'Auto-select (recommended)', value: '' },
                      ...availableConverters.map(c => ({
                        label: `${c.converter_id} (${c.instrument_type})`,
                        value: c.converter_id,
                        description: c.description || ''
                      }))
                    ]}
                    placeholder="Auto-select"
                  />
                </FormField>
              )}
            </SpaceBetween>
          </Container>

          <Container header={<Header variant="h2">Instrument Config Preview</Header>}>
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
              <Button key="download-button" variant="primary" onClick={downloadManifest} disabled={isCustom && (!customManufacturer || !customModel)}>
                Download instrument_config.json
              </Button>
            </SpaceBetween>
          </Container>
        </>
      )}
    </SpaceBetween>
  )
}
