import { useState, useEffect } from 'react'
import Container from '@cloudscape-design/components/container'
import Header from '@cloudscape-design/components/header'
import SpaceBetween from '@cloudscape-design/components/space-between'
import Box from '@cloudscape-design/components/box'
import Badge from '@cloudscape-design/components/badge'
import Button from '@cloudscape-design/components/button'
import Table from '@cloudscape-design/components/table'
import ColumnLayout from '@cloudscape-design/components/column-layout'
import StatusIndicator from '@cloudscape-design/components/status-indicator'
import TextFilter from '@cloudscape-design/components/text-filter'
import Pagination from '@cloudscape-design/components/pagination'
import Alert from '@cloudscape-design/components/alert'

const HISTORY_ENDPOINT = 'https://tqzatn5bse.execute-api.us-east-1.amazonaws.com/prod/history'

function ControlTowerApp() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [filteringText, setFilteringText] = useState('')
  const [currentPageIndex, setCurrentPageIndex] = useState(1)
  const pageSize = 10

  const fetchJobs = async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await fetch(HISTORY_ENDPOINT)
      const data = await resp.json()
      if (data.jobs) {
        setJobs(data.jobs.map(j => ({
          id: j.conversion_id || j.id,
          method: j.method || j.conversion_method || j.source || '-',
          status: j.status || 'unknown',
          timestamp: j.timestamp || '-',
          instrumentType: (j.instrument_type || '-').replace(/_/g, ' '),
          vendor: j.vendor || '-',
          s3Key: j.asm_s3_key || '-',
        })))
      }
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchJobs() }, [])

  // KPIs
  const totalJobs = jobs.length
  const completed = jobs.filter(j => j.status === 'completed').length
  const failed = jobs.filter(j => j.status === 'failed').length
  const successRate = totalJobs > 0 ? ((completed / totalJobs) * 100).toFixed(1) : 0

  // Unique instruments
  const instruments = [...new Set(jobs.map(j => j.instrumentType).filter(t => t !== '-'))]

  // Method breakdown
  const methods = jobs.reduce((acc, j) => {
    const m = j.method
    acc[m] = (acc[m] || 0) + 1
    return acc
  }, {})

  // Filter
  const filtered = jobs.filter(j =>
    j.id.toLowerCase().includes(filteringText.toLowerCase()) ||
    j.instrumentType.toLowerCase().includes(filteringText.toLowerCase()) ||
    j.vendor.toLowerCase().includes(filteringText.toLowerCase()) ||
    j.method.toLowerCase().includes(filteringText.toLowerCase())
  )

  const paginated = filtered.slice(
    (currentPageIndex - 1) * pageSize,
    currentPageIndex * pageSize
  )

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="Real-time view of all conversion and validation jobs"
        actions={
          <Button iconName="refresh" onClick={fetchJobs} loading={loading}>
            Refresh
          </Button>
        }
      >
        Control Tower
      </Header>

      {error && (
        <Alert type="error" header="Failed to load job history">{error}</Alert>
      )}

      {/* KPI Cards */}
      <Container>
        <ColumnLayout columns={4} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">Total Jobs</Box>
            <Box fontSize="display-l" fontWeight="bold">{totalJobs}</Box>
          </div>
          <div>
            <Box variant="awsui-key-label">Success Rate</Box>
            <Box fontSize="display-l" fontWeight="bold" color="text-status-success">
              {successRate}%
            </Box>
            <Box variant="small" color="text-status-inactive">
              {completed} completed / {failed} failed
            </Box>
          </div>
          <div>
            <Box variant="awsui-key-label">Instrument Types</Box>
            <Box fontSize="display-l" fontWeight="bold">{instruments.length}</Box>
            <Box variant="small" color="text-status-inactive">
              {instruments.slice(0, 3).join(', ')}{instruments.length > 3 ? '...' : ''}
            </Box>
          </div>
          <div>
            <Box variant="awsui-key-label">Conversion Methods</Box>
            <SpaceBetween size="xs">
              {Object.entries(methods).map(([m, count]) => (
                <Box key={m} variant="small">{m}: {count}</Box>
              ))}
            </SpaceBetween>
          </div>
        </ColumnLayout>
      </Container>

      {/* Jobs Table */}
      <Table
        columnDefinitions={[
          {
            id: 'id',
            header: 'Conversion ID',
            cell: item => <Box fontWeight="bold">{item.id}</Box>,
            sortingField: 'id',
            width: 220
          },
          {
            id: 'timestamp',
            header: 'Timestamp',
            cell: item => item.timestamp !== '-' ? new Date(item.timestamp).toLocaleString() : '-',
            sortingField: 'timestamp',
            width: 180
          },
          {
            id: 'instrumentType',
            header: 'Instrument Type',
            cell: item => item.instrumentType,
            sortingField: 'instrumentType',
            width: 160
          },
          {
            id: 'vendor',
            header: 'Vendor',
            cell: item => item.vendor,
            sortingField: 'vendor',
            width: 150
          },
          {
            id: 'method',
            header: 'Method',
            cell: item => {
              const colors = {
                'custom-nova-flex2': 'blue',
                'multi-instrument': 'green',
                'ataas-ai': 'grey',
                'custom-converter': 'blue',
              }
              return <Badge color={colors[item.method] || 'grey'}>{item.method}</Badge>
            },
            sortingField: 'method',
            width: 180
          },
          {
            id: 'status',
            header: 'Status',
            cell: item => {
              if (item.status === 'completed') return <StatusIndicator type="success">Completed</StatusIndicator>
              if (item.status === 'failed') return <StatusIndicator type="error">Failed</StatusIndicator>
              return <StatusIndicator type="pending">{item.status}</StatusIndicator>
            },
            sortingField: 'status',
            width: 130
          },
          {
            id: 's3Key',
            header: 'S3 Location',
            cell: item => <Box variant="small" color="text-status-inactive">{item.s3Key}</Box>,
            width: 250
          }
        ]}
        items={paginated}
        loading={loading}
        loadingText="Loading job history..."
        header={
          <Header variant="h2" counter={`(${filtered.length})`}>
            Job History
          </Header>
        }
        filter={
          <TextFilter
            filteringText={filteringText}
            filteringPlaceholder="Search by ID, instrument, vendor, method..."
            onChange={({ detail }) => { setFilteringText(detail.filteringText); setCurrentPageIndex(1) }}
          />
        }
        pagination={
          <Pagination
            currentPageIndex={currentPageIndex}
            pagesCount={Math.ceil(filtered.length / pageSize)}
            onChange={({ detail }) => setCurrentPageIndex(detail.currentPageIndex)}
          />
        }
        empty={
          <Box textAlign="center" color="inherit" padding="l">
            <Box variant="p" color="inherit">
              {loading ? 'Loading...' : 'No conversion jobs found. Run a conversion from the Convert tab to see data here.'}
            </Box>
          </Box>
        }
      />
    </SpaceBetween>
  )
}

export default ControlTowerApp
