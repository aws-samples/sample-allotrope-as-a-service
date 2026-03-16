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
import Link from '@cloudscape-design/components/link'
import TextFilter from '@cloudscape-design/components/text-filter'
import Pagination from '@cloudscape-design/components/pagination'
import CollectionPreferences from '@cloudscape-design/components/collection-preferences'

function ControlTowerApp() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [filteringText, setFilteringText] = useState('')
  const [currentPageIndex, setCurrentPageIndex] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [selectedItems, setSelectedItems] = useState([])

  // Mock data - in production, this would come from an API
  useEffect(() => {
    // Generate mock job data
    const mockJobs = [
      {
        id: 'job-001',
        fileName: 'SampleResults2025-November.csv',
        instrument: 'Nova BioProfile FLEX2',
        type: 'Conversion',
        status: 'Success',
        startTime: '2025-01-30 09:15:23',
        duration: '0.8s',
        measurements: 27,
        errors: 0,
        warnings: 2,
        validationStatus: 'VALID'
      },
      {
        id: 'job-002',
        fileName: 'EndoScanV-Export-20230713.xml',
        instrument: 'Charles River EndoScan-V',
        type: 'Conversion',
        status: 'Success',
        startTime: '2025-01-30 09:18:45',
        duration: '1.2s',
        measurements: 48,
        errors: 0,
        warnings: 3,
        validationStatus: 'VALID'
      },
      {
        id: 'job-003',
        fileName: 'customer_asm_file.json',
        instrument: 'N/A',
        type: 'Validation',
        status: 'Failed',
        startTime: '2025-01-30 09:22:10',
        duration: '0.3s',
        measurements: 4,
        errors: 1,
        warnings: 2,
        validationStatus: 'INVALID'
      },
      {
        id: 'job-004',
        fileName: 'PlateReader-Results-Jan.csv',
        instrument: 'Molecular Devices SoftMax Pro',
        type: 'Conversion',
        status: 'Success',
        startTime: '2025-01-30 09:25:33',
        duration: '0.9s',
        measurements: 96,
        errors: 0,
        warnings: 1,
        validationStatus: 'VALID'
      },
      {
        id: 'job-005',
        fileName: 'CellCount-Batch-05.xlsx',
        instrument: 'Beckman Vi-CELL BLU',
        type: 'Conversion',
        status: 'In Progress',
        startTime: '2025-01-30 09:28:15',
        duration: '-',
        measurements: '-',
        errors: '-',
        warnings: '-',
        validationStatus: 'Pending'
      },
      {
        id: 'job-006',
        fileName: 'QC-Sample-2025-01.json',
        instrument: 'N/A',
        type: 'Validation',
        status: 'Success',
        startTime: '2025-01-30 09:30:42',
        duration: '0.2s',
        measurements: 12,
        errors: 0,
        warnings: 0,
        validationStatus: 'VALID'
      },
      {
        id: 'job-007',
        fileName: 'Unknown-Format.dat',
        instrument: 'Custom Instrument',
        type: 'Conversion',
        status: 'Failed',
        startTime: '2025-01-30 09:32:18',
        duration: '2.1s',
        measurements: 0,
        errors: 1,
        warnings: 0,
        validationStatus: 'INVALID'
      },
      {
        id: 'job-008',
        fileName: 'Spectro-UV-Vis-Data.csv',
        instrument: 'Thermo NanoDrop Eight',
        type: 'Conversion',
        status: 'Success',
        startTime: '2025-01-30 09:35:55',
        duration: '0.7s',
        measurements: 8,
        errors: 0,
        warnings: 1,
        validationStatus: 'VALID'
      }
    ]
    setJobs(mockJobs)
  }, [])

  // Calculate KPIs
  const totalJobs = jobs.length
  const successfulJobs = jobs.filter(j => j.status === 'Success').length
  const failedJobs = jobs.filter(j => j.status === 'Failed').length
  const inProgressJobs = jobs.filter(j => j.status === 'In Progress').length
  const successRate = totalJobs > 0 ? ((successfulJobs / totalJobs) * 100).toFixed(1) : 0
  const totalMeasurements = jobs.reduce((sum, j) => sum + (typeof j.measurements === 'number' ? j.measurements : 0), 0)
  const avgDuration = jobs
    .filter(j => j.duration !== '-')
    .reduce((sum, j, _, arr) => sum + parseFloat(j.duration) / arr.length, 0)
    .toFixed(2)

  // Filter jobs
  const filteredJobs = jobs.filter(job =>
    job.fileName.toLowerCase().includes(filteringText.toLowerCase()) ||
    job.instrument.toLowerCase().includes(filteringText.toLowerCase()) ||
    job.type.toLowerCase().includes(filteringText.toLowerCase()) ||
    job.status.toLowerCase().includes(filteringText.toLowerCase())
  )

  // Paginate
  const paginatedJobs = filteredJobs.slice(
    (currentPageIndex - 1) * pageSize,
    currentPageIndex * pageSize
  )

  const getStatusIndicator = (status) => {
    switch (status) {
      case 'Success':
        return <StatusIndicator type="success">Success</StatusIndicator>
      case 'Failed':
        return <StatusIndicator type="error">Failed</StatusIndicator>
      case 'In Progress':
        return <StatusIndicator type="in-progress">In Progress</StatusIndicator>
      default:
        return <StatusIndicator type="pending">Pending</StatusIndicator>
    }
  }

  const getValidationBadge = (status) => {
    switch (status) {
      case 'VALID':
        return <Badge color="green">VALID</Badge>
      case 'INVALID':
        return <Badge color="red">INVALID</Badge>
      case 'Pending':
        return <Badge color="grey">Pending</Badge>
      default:
        return <Badge>Unknown</Badge>
    }
  }

  const columnDefinitions = [
    {
      id: 'id',
      header: 'Job ID',
      cell: item => <Link href="#">{item.id}</Link>,
      sortingField: 'id',
      width: 100
    },
    {
      id: 'fileName',
      header: 'File Name',
      cell: item => item.fileName,
      sortingField: 'fileName',
      width: 250
    },
    {
      id: 'instrument',
      header: 'Instrument',
      cell: item => item.instrument,
      sortingField: 'instrument',
      width: 200
    },
    {
      id: 'type',
      header: 'Type',
      cell: item => <Badge color={item.type === 'Conversion' ? 'blue' : 'grey'}>{item.type}</Badge>,
      sortingField: 'type',
      width: 120
    },
    {
      id: 'status',
      header: 'Status',
      cell: item => getStatusIndicator(item.status),
      sortingField: 'status',
      width: 120
    },
    {
      id: 'startTime',
      header: 'Start Time',
      cell: item => item.startTime,
      sortingField: 'startTime',
      width: 180
    },
    {
      id: 'duration',
      header: 'Duration',
      cell: item => item.duration,
      sortingField: 'duration',
      width: 100
    },
    {
      id: 'measurements',
      header: 'Measurements',
      cell: item => item.measurements,
      sortingField: 'measurements',
      width: 120
    },
    {
      id: 'errors',
      header: 'Errors',
      cell: item => (
        <Box color={item.errors > 0 ? 'text-status-error' : 'text-status-success'}>
          {item.errors}
        </Box>
      ),
      sortingField: 'errors',
      width: 80
    },
    {
      id: 'warnings',
      header: 'Warnings',
      cell: item => (
        <Box color={item.warnings > 0 ? 'text-status-warning' : 'text-status-success'}>
          {item.warnings}
        </Box>
      ),
      sortingField: 'warnings',
      width: 100
    },
    {
      id: 'validationStatus',
      header: 'Validation',
      cell: item => getValidationBadge(item.validationStatus),
      sortingField: 'validationStatus',
      width: 120
    }
  ]

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="Monitor all conversion and validation jobs across the system"
        actions={
          <Button iconName="refresh" onClick={() => setLoading(true)}>
            Refresh
          </Button>
        }
      >
        Control Tower
      </Header>

      {/* KPI Cards */}
      <Container>
        <ColumnLayout columns={4} variant="text-grid">
          <div>
            <Box variant="awsui-key-label">Total Jobs</Box>
            <Box fontSize="display-l" fontWeight="bold">
              {totalJobs}
            </Box>
            <Box variant="small" color="text-status-inactive">
              All time
            </Box>
          </div>
          <div>
            <Box variant="awsui-key-label">Success Rate</Box>
            <Box fontSize="display-l" fontWeight="bold" color="text-status-success">
              {successRate}%
            </Box>
            <Box variant="small" color="text-status-inactive">
              {successfulJobs} successful / {failedJobs} failed
            </Box>
          </div>
          <div>
            <Box variant="awsui-key-label">Total Measurements</Box>
            <Box fontSize="display-l" fontWeight="bold">
              {totalMeasurements}
            </Box>
            <Box variant="small" color="text-status-inactive">
              Across all jobs
            </Box>
          </div>
          <div>
            <Box variant="awsui-key-label">Avg Duration</Box>
            <Box fontSize="display-l" fontWeight="bold">
              {avgDuration}s
            </Box>
            <Box variant="small" color="text-status-inactive">
              Per job
            </Box>
          </div>
        </ColumnLayout>
      </Container>

      {/* Status Summary */}
      <Container header={<Header variant="h2">Status Summary</Header>}>
        <ColumnLayout columns={3} variant="text-grid">
          <div>
            <StatusIndicator type="success">Successful</StatusIndicator>
            <Box fontSize="heading-xl" padding={{ top: 'xs' }}>
              {successfulJobs}
            </Box>
          </div>
          <div>
            <StatusIndicator type="error">Failed</StatusIndicator>
            <Box fontSize="heading-xl" padding={{ top: 'xs' }}>
              {failedJobs}
            </Box>
          </div>
          <div>
            <StatusIndicator type="in-progress">In Progress</StatusIndicator>
            <Box fontSize="heading-xl" padding={{ top: 'xs' }}>
              {inProgressJobs}
            </Box>
          </div>
        </ColumnLayout>
      </Container>

      {/* Jobs Table */}
      <Table
        columnDefinitions={columnDefinitions}
        items={paginatedJobs}
        loading={loading}
        loadingText="Loading jobs..."
        selectionType="multi"
        selectedItems={selectedItems}
        onSelectionChange={({ detail }) => setSelectedItems(detail.selectedItems)}
        header={
          <Header
            variant="h2"
            counter={`(${filteredJobs.length})`}
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Button disabled={selectedItems.length === 0}>
                  View Details
                </Button>
                <Button disabled={selectedItems.length === 0}>
                  Download Reports
                </Button>
                <Button disabled={selectedItems.length === 0}>
                  Retry Failed
                </Button>
              </SpaceBetween>
            }
          >
            Job History
          </Header>
        }
        filter={
          <TextFilter
            filteringText={filteringText}
            filteringPlaceholder="Search jobs..."
            onChange={({ detail }) => setFilteringText(detail.filteringText)}
          />
        }
        pagination={
          <Pagination
            currentPageIndex={currentPageIndex}
            pagesCount={Math.ceil(filteredJobs.length / pageSize)}
            onChange={({ detail }) => setCurrentPageIndex(detail.currentPageIndex)}
          />
        }
        preferences={
          <CollectionPreferences
            title="Preferences"
            confirmLabel="Confirm"
            cancelLabel="Cancel"
            preferences={{
              pageSize: pageSize
            }}
            pageSizePreference={{
              title: 'Page size',
              options: [
                { value: 10, label: '10 jobs' },
                { value: 20, label: '20 jobs' },
                { value: 50, label: '50 jobs' }
              ]
            }}
            onConfirm={({ detail }) => setPageSize(detail.pageSize)}
          />
        }
        empty={
          <Box textAlign="center" color="inherit">
            <Box padding={{ bottom: 's' }} variant="p" color="inherit">
              No jobs found
            </Box>
            <Button>Start a conversion</Button>
          </Box>
        }
      />
    </SpaceBetween>
  )
}

export default ControlTowerApp
