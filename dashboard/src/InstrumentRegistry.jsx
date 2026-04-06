import { useState, useEffect } from 'react'
import Container from '@cloudscape-design/components/container'
import Header from '@cloudscape-design/components/header'
import SpaceBetween from '@cloudscape-design/components/space-between'
import Table from '@cloudscape-design/components/table'
import Box from '@cloudscape-design/components/box'
import Badge from '@cloudscape-design/components/badge'
import Input from '@cloudscape-design/components/input'
import Select from '@cloudscape-design/components/select'
import Button from '@cloudscape-design/components/button'
import Modal from '@cloudscape-design/components/modal'
import FormField from '@cloudscape-design/components/form-field'
import Alert from '@cloudscape-design/components/alert'
import { ENDPOINTS } from './config'
import instrumentsData from './data/instruments.json'

export default function InstrumentRegistry() {
  const [allInstruments, setAllInstruments] = useState(instrumentsData)
  const [searchTerm, setSearchTerm] = useState('')
  const [typeFilter, setTypeFilter] = useState({ label: 'All Types', value: 'all' })
  const [selectedInstrument, setSelectedInstrument] = useState(null)
  const [showAliasModal, setShowAliasModal] = useState(false)
  const [newAlias, setNewAlias] = useState('')
  const [customerAliases, setCustomerAliases] = useState(() => {
    // Load from localStorage on mount
    const saved = localStorage.getItem('customerAliases')
    return saved ? JSON.parse(saved) : {}
  })

  const typeOptions = [
    { label: 'All Types', value: 'all' },
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

  useEffect(() => {
    const fetchRegistered = async () => {
      try {
        const resp = await fetch(`${ENDPOINTS.customConverter}/list`)
        const data = await resp.json()
        const registered = (data.converters || []).map(c => ({
          canonical_id: `registered-${c.converter_id}`,
          vendor_id: c.vendor || '',
          name: c.model || c.converter_id,
          manufacturer: c.vendor || '',
          instrument_type: c.instrument_type || 'unknown',
          allotropy_supported: false,
          converter_type: 'custom',
          converter_id: c.converter_id,
          aliases: [],
          registry_status: c.status,
          source: 'registered'
        }))
        // Merge: static instruments + registered (avoid duplicates by vendor_id)
        const staticIds = new Set(instrumentsData.map(i => i.vendor_id))
        const unique = registered.filter(r => !staticIds.has(r.vendor_id))
        setAllInstruments([...instrumentsData, ...unique])
      } catch (e) {
        // If fetch fails, just use static data
      }
    }
    fetchRegistered()
  }, [])

  const filteredInstruments = allInstruments.filter(inst => {
    const matchesSearch = searchTerm === '' || 
      inst.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inst.manufacturer.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inst.aliases.some(a => a.toLowerCase().includes(searchTerm.toLowerCase()))
    
    const matchesType = typeFilter.value === 'all' || inst.instrument_type === typeFilter.value
    
    return matchesSearch && matchesType
  })

  const addCustomerAlias = () => {
    if (selectedInstrument && newAlias.trim()) {
      const updated = {
        ...customerAliases,
        [selectedInstrument.canonical_id]: [
          ...(customerAliases[selectedInstrument.canonical_id] || []),
          newAlias.trim()
        ]
      }
      setCustomerAliases(updated)
      localStorage.setItem('customerAliases', JSON.stringify(updated)) // Save to localStorage
      setNewAlias('')
      setShowAliasModal(false)
    }
  }

  return (
    <SpaceBetween size="l">
      <Alert type="info">
        Browse 18+ instruments supported by allotropy library and custom converters. Add your own aliases to match your lab's naming conventions.
      </Alert>

      <Container>
        <SpaceBetween size="m">
          <Header
            variant="h2"
            counter={`(${filteredInstruments.length})`}
            description="Search and filter instruments from the registry"
          >
            Instrument Registry
          </Header>

          <SpaceBetween direction="horizontal" size="m">
            <FormField label="Search">
              <Input
                value={searchTerm}
                onChange={({ detail }) => setSearchTerm(detail.value)}
                placeholder="Search by name, manufacturer, or alias..."
                type="search"
              />
            </FormField>

            <FormField label="Filter by Type">
              <Select
                selectedOption={typeFilter}
                onChange={({ detail }) => setTypeFilter(detail.selectedOption)}
                options={typeOptions}
              />
            </FormField>
          </SpaceBetween>

          <Table
            columnDefinitions={[
              {
                id: 'name',
                header: 'Instrument',
                cell: item => item.name,
                sortingField: 'name'
              },
              {
                id: 'manufacturer',
                header: 'Manufacturer',
                cell: item => item.manufacturer,
                sortingField: 'manufacturer'
              },
              {
                id: 'type',
                header: 'Type',
                cell: item => item.instrument_type.replace('_', ' '),
                sortingField: 'instrument_type'
              },
              {
                id: 'converter',
                header: 'Converter Type',
                cell: item => {
                  if (item.source === 'registered') {
                    return <SpaceBetween direction="horizontal" size="xs">
                      <Badge color="blue">Custom</Badge>
                      <Badge color={item.registry_status === 'APPROVED' ? 'green' : 'grey'}>{item.registry_status}</Badge>
                    </SpaceBetween>
                  }
                  return item.allotropy_supported 
                    ? <Badge color="green">Allotropy</Badge>
                    : <Badge color="blue">Custom</Badge>
                }
              },
              {
                id: 'converter_id',
                header: 'Converter ID',
                cell: item => item.converter_id || '-'
              }
            ]}
            items={filteredInstruments}
            selectionType="single"
            selectedItems={selectedInstrument ? [selectedInstrument] : []}
            onSelectionChange={({ detail }) => setSelectedInstrument(detail.selectedItems[0])}
            sortingDisabled={false}
            empty={
              <Box textAlign="center" color="inherit">
                <b>No instruments found</b>
                <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                  Try adjusting your search or filter.
                </Box>
              </Box>
            }
          />
        </SpaceBetween>
      </Container>

      {selectedInstrument && (
        <Container header={<Header variant="h2">{selectedInstrument.name}</Header>}>
          <SpaceBetween size="m">
            <SpaceBetween size="s">
              <Box>
                <Box variant="awsui-key-label">Canonical ID</Box>
                <Box>{selectedInstrument.canonical_id}</Box>
              </Box>
              <Box>
                <Box variant="awsui-key-label">Vendor ID</Box>
                <Box>{selectedInstrument.vendor_id}</Box>
              </Box>
              <Box>
                <Box variant="awsui-key-label">Manufacturer</Box>
                <Box>{selectedInstrument.manufacturer}</Box>
              </Box>
              <Box>
                <Box variant="awsui-key-label">Type</Box>
                <Box>{selectedInstrument.instrument_type.replace('_', ' ')}</Box>
              </Box>
              <Box>
                <Box variant="awsui-key-label">Allotropy Support</Box>
                <Box>{selectedInstrument.allotropy_supported ? '✓ Available' : '✗ Not Available'}</Box>
              </Box>
            </SpaceBetween>

            <Box>
              <Box variant="awsui-key-label">Known Aliases</Box>
              <Box>
                {selectedInstrument.aliases.map((alias, idx) => (
                  <Badge key={idx}>{alias}</Badge>
                ))}
              </Box>
            </Box>

            {customerAliases[selectedInstrument.canonical_id] && (
              <Box>
                <Box variant="awsui-key-label">Your Aliases</Box>
                <Box>
                  {customerAliases[selectedInstrument.canonical_id].map((alias, idx) => (
                    <Badge key={idx} color="blue">{alias}</Badge>
                  ))}
                </Box>
              </Box>
            )}

            <SpaceBetween direction="horizontal" size="xs">
              <Button onClick={() => setShowAliasModal(true)}>
                Add Your Alias
              </Button>
            </SpaceBetween>
          </SpaceBetween>
        </Container>
      )}

      <Modal
        visible={showAliasModal}
        onDismiss={() => setShowAliasModal(false)}
        header="Add Your Alias"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button variant="link" onClick={() => setShowAliasModal(false)}>
                Cancel
              </Button>
              <Button variant="primary" onClick={addCustomerAlias}>
                Add Alias
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="m">
          <Box>
            Adding alias for: <strong>{selectedInstrument?.name}</strong>
          </Box>
          <FormField
            label="Your Alias"
            description="What you call this instrument in your lab"
          >
            <Input
              value={newAlias}
              onChange={({ detail }) => setNewAlias(detail.value)}
              placeholder="e.g., Lab 3 FLEX2"
            />
          </FormField>
          <Alert type="info">
            This alias will be recognized when you upload files or create manifests.
          </Alert>
        </SpaceBetween>
      </Modal>
    </SpaceBetween>
  )
}
