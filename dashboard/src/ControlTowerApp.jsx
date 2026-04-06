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

import Select from '@cloudscape-design/components/select'
import DateRangePicker from '@cloudscape-design/components/date-range-picker'
import FormField from '@cloudscape-design/components/form-field'

import { ENDPOINTS } from './config'

function ControlTowerApp() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [filteringText, setFilteringText] = useState('')
  const [instrumentFilter, setInstrumentFilter] = useState({ label: 'All Instruments', value: 'all' })
  const [dateRange, setDateRange] = useState(null)
  const [currentPageIndex, setCurrentPageIndex] = useState(1)
  const pageSize = 10

  const fetchJobs = async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await fetch(`${ENDPOINTS.unifiedConverter}/history`)
      const data = await resp.json()
      if (data.jobs) {
        setJobs(data.jobs.map(j => ({
          id: j.conversion_id || j.id,
          type: j.type || (j.conversion_id?.startsWith('VALIDATE') ? 'validation' : 'conversion'),
          method: j.method || j.conversion_method || j.source || '-',
          status: j.status || 'unknown',
          timestamp: j.timestamp || '-',
          instrumentType: (j.instrument_type || j.technique || '-').replace(/_/g, ' '),
          instrumentModel: j.instrument_model || j.model || '-',
          vendor: j.vendor || j.converter_used || '-',
          fileName: j.file_name || '-',
          errorCount: j.error_count ?? '-',
          warningCount: j.warning_count ?? '-',
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
  const completed = jobs.filter(j => ['completed', 'valid', 'pass'].includes(j.status)).length
  const failed = jobs.filter(j => ['failed', 'invalid', 'fail'].includes(j.status)).length
  const successRate = totalJobs > 0 ? ((completed / totalJobs) * 100).toFixed(1) : 0

  // Type breakdown
  const conversions = jobs.filter(j => j.type === 'conversion').length
  const validations = jobs.filter(j => j.type === 'validation').length

  // Unique instruments
  const instruments = [...new Set(jobs.map(j => j.instrumentType).filter(t => t !== '-'))]

  // Method breakdown
  const methods = jobs.reduce((acc, j) => {
    const m = j.method
    acc[m] = (acc[m] || 0) + 1
    return acc
  }, {})

  // Unique instrument models for filter dropdown
  const instrumentModels = [...new Set(jobs.map(j => j.instrumentModel).filter(m => m !== '-'))]
  const instrumentFilterOptions = [
    { label: 'All Instruments', value: 'all' },
    ...instrumentModels.map(m => ({ label: m, value: m }))
  ]

  // Filter
  const filtered = jobs.filter(j => {
    const matchesText = !filteringText ||
      j.id.toLowerCase().includes(filteringText.toLowerCase()) ||
      j.instrumentType.toLowerCase().includes(filteringText.toLowerCase()) ||
      j.instrumentModel.toLowerCase().includes(filteringText.toLowerCase()) ||
      j.vendor.toLowerCase().includes(filteringText.toLowerCase()) ||
      j.method.toLowerCase().includes(filteringText.toLowerCase())

    const matchesInstrument = instrumentFilter.value === 'all' ||
      j.instrumentModel === instrumentFilter.value

    let matchesDate = true
    if (dateRange && j.timestamp !== '-') {
      const jobDate = new Date(j.timestamp)
      if (dateRange.type === 'absolute') {
        const start = new Date(dateRange.startDate)
        const end = new Date(dateRange.endDate)
        end.setHours(23, 59, 59, 999)
        matchesDate = jobDate >= start && jobDate <= end
      } else if (dateRange.type === 'relative') {
        const now = new Date()
        const amount = dateRange.amount
        const unit = dateRange.unit
        const cutoff = new Date(now)
        if (unit === 'day') cutoff.setDate(cutoff.getDate() - amount)
        else if (unit === 'week') cutoff.setDate(cutoff.getDate() - amount * 7)
        else if (unit === 'month') cutoff.setMonth(cutoff.getMonth() - amount)
        matchesDate = jobDate >= cutoff
      }
    }

    return matchesText && matchesInstrument && matchesDate
  })

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
            <Box variant="awsui-key-label">Jobs by Type</Box>
            <SpaceBetween size="xs">
              <Box variant="small">Conversions: {conversions}</Box>
              <Box variant="small">Validations: {validations}</Box>
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
            id: 'type',
            header: 'Type',
            cell: item => <Badge color={item.type === 'validation' ? 'grey' : 'blue'}>{item.type}</Badge>,
            sortingField: 'type',
            width: 120
          },
          {
            id: 'instrumentModel',
            header: 'Instrument',
            cell: item => item.instrumentModel,
            sortingField: 'instrumentModel',
            width: 160
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
              if (['completed', 'valid', 'pass'].includes(item.status)) return <StatusIndicator type="success">{item.status}</StatusIndicator>
              if (['failed', 'invalid', 'fail'].includes(item.status)) return <StatusIndicator type="error">{item.status}</StatusIndicator>
              return <StatusIndicator type="pending">{item.status}</StatusIndicator>
            },
            sortingField: 'status',
            width: 130
          },
          {
            id: 'errors',
            header: 'Errors',
            cell: item => item.errorCount !== '-' ? (
              <Box color={item.errorCount > 0 ? 'text-status-error' : 'text-status-success'}>{item.errorCount}</Box>
            ) : '-',
            width: 80
          },
          {
            id: 'warnings',
            header: 'Warnings',
            cell: item => item.warningCount !== '-' ? (
              <Box color={item.warningCount > 0 ? 'text-status-warning' : 'text-status-success'}>{item.warningCount}</Box>
            ) : '-',
            width: 90
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
          <SpaceBetween direction="horizontal" size="m">
            <TextFilter
              filteringText={filteringText}
              filteringPlaceholder="Search by ID, vendor, method..."
              onChange={({ detail }) => { setFilteringText(detail.filteringText); setCurrentPageIndex(1) }}
            />
            <Select
              selectedOption={instrumentFilter}
              onChange={({ detail }) => { setInstrumentFilter(detail.selectedOption); setCurrentPageIndex(1) }}
              options={instrumentFilterOptions}
              placeholder="Filter by instrument"
            />
            <DateRangePicker
              value={dateRange}
              onChange={({ detail }) => { setDateRange(detail.value); setCurrentPageIndex(1) }}
              placeholder="Filter by date"
              relativeOptions={[
                { key: 'today', amount: 1, unit: 'day', type: 'relative' },
                { key: 'week', amount: 1, unit: 'week', type: 'relative' },
                { key: 'month', amount: 1, unit: 'month', type: 'relative' },
                { key: '3months', amount: 3, unit: 'month', type: 'relative' },
              ]}
              i18nStrings={{
                todayAriaLabel: 'Today',
                nextMonthAriaLabel: 'Next month',
                previousMonthAriaLabel: 'Previous month',
                customRelativeRangeDurationLabel: 'Duration',
                customRelativeRangeDurationPlaceholder: 'Enter duration',
                customRelativeRangeOptionLabel: 'Custom range',
                customRelativeRangeOptionDescription: 'Set a custom range in the past',
                customRelativeRangeUnitLabel: 'Unit of time',
                formatRelativeRange: (e) => {
                  const unit = e.amount === 1 ? e.unit : `${e.unit}s`
                  return `Last ${e.amount} ${unit}`
                },
                formatUnit: (unit, value) => value === 1 ? unit : `${unit}s`,
                relativeModeTitle: 'Relative range',
                absoluteModeTitle: 'Absolute range',
                relativeRangeSelectionHeading: 'Choose a range',
                startDateLabel: 'Start date',
                startTimeLabel: 'Start time',
                endDateLabel: 'End date',
                endTimeLabel: 'End time',
                dateTimeConstraintText: '',
                clearButtonLabel: 'Clear',
                cancelButtonLabel: 'Cancel',
                applyButtonLabel: 'Apply',
              }}
              isValidRange={(range) => {
                if (range.type === 'absolute' && (!range.startDate || !range.endDate)) {
                  return { valid: false, errorMessage: 'Select start and end dates' }
                }
                return { valid: true }
              }}
            />
          </SpaceBetween>
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
