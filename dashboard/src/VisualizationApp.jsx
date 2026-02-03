import { useState, useEffect } from 'react'
import Container from '@cloudscape-design/components/container'
import Header from '@cloudscape-design/components/header'
import SpaceBetween from '@cloudscape-design/components/space-between'
import Grid from '@cloudscape-design/components/grid'
import Box from '@cloudscape-design/components/box'
import Badge from '@cloudscape-design/components/badge'
import Table from '@cloudscape-design/components/table'
import Select from '@cloudscape-design/components/select'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

function VisualizationApp() {
  const [selectedInstrument, setSelectedInstrument] = useState({ label: 'All Instruments', value: 'all' })
  const [asmData] = useState([
    { id: 1, instrument: 'Nova FLEX2', sample: 'XB21-720-0300', date: '2025-11-01', pH: 7.183, pO2: 94.5, pCO2: 31.4, glucose: 8.21, lactate: 0.25, valid: true },
    { id: 2, instrument: 'Nova FLEX2', sample: 'XB22-720-0270', date: '2025-11-01', pH: 7.164, pO2: 63.1, pCO2: 24.0, glucose: 7.87, lactate: 0.48, valid: true },
    { id: 3, instrument: 'Nova FLEX2', sample: 'XB21-0698-0120', date: '2025-11-02', pH: 6.976, pO2: 70.7, pCO2: 11.1, glucose: 7.00, lactate: 0.95, valid: true },
    { id: 4, instrument: 'Nova FLEX2', sample: 'D_FD_CE_N-5', date: '2025-07-02', pH: 7.156, pO2: 164.7, pCO2: 33.0, glucose: 4.91, lactate: 1.12, valid: true },
    { id: 5, instrument: 'Nova FLEX2', sample: 'D_FD_CE_N-5B', date: '2025-07-02', pH: 7.095, pO2: 166.5, pCO2: 35.8, glucose: 4.71, lactate: 1.26, valid: true },
    { id: 6, instrument: 'Nova FLEX2', sample: 'D_SD_CE_N-4', date: '2025-07-02', pH: 7.233, pO2: 205.6, pCO2: 58.8, glucose: 6.52, lactate: 0.11, valid: true },
  ])

  const instruments = [
    { label: 'All Instruments', value: 'all' },
    { label: 'Nova FLEX2', value: 'nova_flex2' },
    { label: 'EndoScan-V', value: 'endoscan' },
    { label: 'Wyatt ASTRA', value: 'wyatt' }
  ]

  const filteredData = selectedInstrument.value === 'all' 
    ? asmData 
    : asmData.filter(d => d.instrument.toLowerCase().includes(selectedInstrument.value.replace('_', ' ')))

  const validCount = filteredData.filter(d => d.valid).length
  const totalCount = filteredData.length
  const validationRate = totalCount > 0 ? ((validCount / totalCount) * 100).toFixed(1) : 0

  const chartData = filteredData.map(d => ({
    sample: d.sample.substring(0, 10),
    pH: d.pH,
    glucose: d.glucose,
    lactate: d.lactate
  }))

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="Real-time monitoring and analysis of multi-instrument ASM data"
        actions={
          <Select
            selectedOption={selectedInstrument}
            onChange={({ detail }) => setSelectedInstrument(detail.selectedOption)}
            options={instruments}
            placeholder="Select instrument"
          />
        }
      >
        Multi-Instrument Dashboard
      </Header>

      {/* KPI Cards */}
      <Grid gridDefinition={[{ colspan: 3 }, { colspan: 3 }, { colspan: 3 }, { colspan: 3 }]}>
        <Container>
          <Box variant="h3" padding={{ bottom: 's' }}>Total Samples</Box>
          <Box variant="h1" color="text-status-info">{totalCount}</Box>
          <Box variant="small" color="text-status-inactive">Across all instruments</Box>
        </Container>

        <Container>
          <Box variant="h3" padding={{ bottom: 's' }}>Valid ASM Files</Box>
          <Box variant="h1" color="text-status-success">{validCount}</Box>
          <Box variant="small" color="text-status-inactive">{validationRate}% validation rate</Box>
        </Container>

        <Container>
          <Box variant="h3" padding={{ bottom: 's' }}>Instruments</Box>
          <Box variant="h1" color="text-status-info">3</Box>
          <Box variant="small" color="text-status-inactive">Nova FLEX2, EndoScan-V, Wyatt ASTRA</Box>
        </Container>

        <Container>
          <Box variant="h3" padding={{ bottom: 's' }}>Avg Processing Time</Box>
          <Box variant="h1" color="text-status-success">&lt;1s</Box>
          <Box variant="small" color="text-status-inactive">Per file conversion</Box>
        </Container>
      </Grid>

      {/* Charts */}
      <Grid gridDefinition={[{ colspan: 6 }, { colspan: 6 }]}>
        <Container header={<Header variant="h2">pH Trends</Header>}>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="sample" />
              <YAxis domain={[6.5, 7.5]} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="pH" stroke="#0972d3" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </Container>

        <Container header={<Header variant="h2">Metabolite Levels</Header>}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="sample" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="glucose" fill="#0972d3" name="Glucose (g/L)" />
              <Bar dataKey="lactate" fill="#037f0c" name="Lactate (g/L)" />
            </BarChart>
          </ResponsiveContainer>
        </Container>
      </Grid>

      {/* Data Table */}
      <Container header={<Header variant="h2">Sample Data</Header>}>
        <Table
          columnDefinitions={[
            { id: 'sample', header: 'Sample ID', cell: item => item.sample, sortingField: 'sample' },
            { id: 'instrument', header: 'Instrument', cell: item => item.instrument },
            { id: 'date', header: 'Date', cell: item => item.date, sortingField: 'date' },
            { id: 'pH', header: 'pH', cell: item => item.pH.toFixed(3) },
            { id: 'pO2', header: 'pO2 (mmHg)', cell: item => item.pO2.toFixed(1) },
            { id: 'pCO2', header: 'pCO2 (mmHg)', cell: item => item.pCO2.toFixed(1) },
            { id: 'glucose', header: 'Glucose (g/L)', cell: item => item.glucose.toFixed(2) },
            { id: 'lactate', header: 'Lactate (g/L)', cell: item => item.lactate.toFixed(2) },
            { id: 'valid', header: 'Validation', cell: item => item.valid ? <Badge color="green">Valid</Badge> : <Badge color="red">Invalid</Badge> }
          ]}
          items={filteredData}
          sortingDisabled={false}
          empty={
            <Box textAlign="center" color="inherit">
              <b>No samples</b>
              <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                No samples to display.
              </Box>
            </Box>
          }
        />
      </Container>
    </SpaceBetween>
  )
}

export default VisualizationApp
