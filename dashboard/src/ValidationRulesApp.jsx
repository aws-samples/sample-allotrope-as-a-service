import { useState, useEffect } from 'react'
import Container from '@cloudscape-design/components/container'
import Header from '@cloudscape-design/components/header'
import SpaceBetween from '@cloudscape-design/components/space-between'
import Box from '@cloudscape-design/components/box'
import Badge from '@cloudscape-design/components/badge'
import Button from '@cloudscape-design/components/button'
import Table from '@cloudscape-design/components/table'
import Modal from '@cloudscape-design/components/modal'
import FormField from '@cloudscape-design/components/form-field'
import Input from '@cloudscape-design/components/input'
import Select from '@cloudscape-design/components/select'
import Textarea from '@cloudscape-design/components/textarea'
import FileUpload from '@cloudscape-design/components/file-upload'
import Alert from '@cloudscape-design/components/alert'
import Toggle from '@cloudscape-design/components/toggle'
import Tabs from '@cloudscape-design/components/tabs'
import ColumnLayout from '@cloudscape-design/components/column-layout'
import ExpandableSection from '@cloudscape-design/components/expandable-section'
import StatusIndicator from '@cloudscape-design/components/status-indicator'

import { ENDPOINTS } from './config'
import TEMPLATE from '../public/docs/asm-validation-template-v1.json'

const LEVEL_COLORS = { L1: 'red', L2: 'blue', L3: 'green', L4: 'grey' }
const CHECK_TYPES = [
  { value: 'field_required', label: 'Field Required' },
  { value: 'field_not_empty', label: 'Field Not Empty' },
  { value: 'value_in_list', label: 'Value In List' },
  { value: 'value_matches_pattern', label: 'Value Matches Pattern' },
  { value: 'path_exists', label: 'Path Exists' },
  { value: 'conditional_required', label: 'Conditional Required' },
  { value: 'count_min', label: 'Minimum Count' },
  { value: 'value_equals', label: 'Value Equals' },
  { value: 'key_not_matches_pattern', label: 'Key Not Matches Pattern' },
]

function ValidationRulesApp() {
  const [ruleSets, setRuleSets] = useState([])
  const [activeRuleSet, setActiveRuleSet] = useState(null)
  const [showImportModal, setShowImportModal] = useState(false)
  const [showAddRuleModal, setShowAddRuleModal] = useState(false)
  const [importFile, setImportFile] = useState([])
  const [alert, setAlert] = useState(null)
  const [editingRuleSet, setEditingRuleSet] = useState(null)
  const [activeSubTab, setActiveSubTab] = useState('manage')

  // New rule form state
  const [newRule, setNewRule] = useState({
    rule_id: '',
    name: '',
    level: { label: 'L3', value: 'L3' },
    check: { label: 'Field Required', value: 'field_required' },
    path: '',
    field: '',
    pattern: '',
    severity: { label: 'Error', value: 'error' },
    message: '',
    reference: '',
    note: ''
  })

  const [loading, setLoading] = useState(true)

  // Load rule sets from API
  useEffect(() => {
    fetchRuleSets()
  }, [])

  const fetchRuleSets = async () => {
    try {
      setLoading(true)
      const resp = await fetch(`${ENDPOINTS.customConverter}/rule-sets`)
      const data = await resp.json()
      setRuleSets(data.rule_sets || [])
    } catch (e) {
      setAlert({ type: 'error', message: `Failed to load rule sets: ${e.message}` })
    } finally {
      setLoading(false)
    }
  }

  const saveRuleSetToAPI = async (ruleSet) => {
    try {
      await fetch(`${ENDPOINTS.customConverter}/rule-sets`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ruleSet)
      })
    } catch (e) {
      setAlert({ type: 'error', message: `Failed to save rule set: ${e.message}` })
    }
  }

  const deleteRuleSetFromAPI = async (ruleSetId) => {
    try {
      await fetch(`${ENDPOINTS.customConverter}/rule-sets`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ rule_set_id: ruleSetId })
      })
    } catch (e) {
      setAlert({ type: 'error', message: `Failed to delete rule set: ${e.message}` })
    }
  }

  const loadTemplate = () => {
    const templateCopy = JSON.parse(JSON.stringify(TEMPLATE))
    templateCopy.rule_set_id = `custom-rules-${Date.now()}`
    templateCopy.name = 'My Validation Rules (from template)'
    templateCopy.author = ''
    setEditingRuleSet(templateCopy)
    setAlert({ type: 'success', message: 'Template loaded with 22 rules. Customize and save when ready.' })
  }

  const importRuleSet = async () => {
    if (!importFile.length) return
    try {
      const content = await importFile[0].text()
      const ruleSet = JSON.parse(content)
      if (!ruleSet.rule_set_id || !ruleSet.rules) {
        setAlert({ type: 'error', message: 'Invalid rule set file. Must contain rule_set_id and rules array.' })
        return
      }
      setEditingRuleSet(ruleSet)
      setShowImportModal(false)
      setImportFile([])
      setAlert({ type: 'success', message: `Imported "${ruleSet.name}" with ${ruleSet.rules.length} rules.` })
    } catch (e) {
      setAlert({ type: 'error', message: `Failed to parse file: ${e.message}` })
    }
  }

  const saveRuleSet = async () => {
    if (!editingRuleSet) return
    if (!editingRuleSet.rule_set_id || !editingRuleSet.name) {
      setAlert({ type: 'error', message: 'Rule set must have an ID and name.' })
      return
    }
    const existing = ruleSets.find(r => r.rule_set_id === editingRuleSet.rule_set_id)
    const toSave = { ...editingRuleSet, enabled: existing ? existing.enabled : true }
    await saveRuleSetToAPI(toSave)
    await fetchRuleSets()
    setAlert({ type: 'success', message: `Rule set "${editingRuleSet.name}" saved with ${editingRuleSet.rules.length} rules.` })
  }

  const toggleRuleSet = async (id) => {
    const rs = ruleSets.find(r => r.rule_set_id === id)
    if (rs) {
      await saveRuleSetToAPI({ ...rs, enabled: !rs.enabled })
      await fetchRuleSets()
    }
  }

  const deleteRuleSet = async (id) => {
    await deleteRuleSetFromAPI(id)
    if (editingRuleSet?.rule_set_id === id) setEditingRuleSet(null)
    await fetchRuleSets()
    setAlert({ type: 'info', message: 'Rule set deleted.' })
  }

  const downloadRuleSet = (ruleSet) => {
    const blob = new Blob([JSON.stringify(ruleSet, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${ruleSet.rule_set_id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const addRule = () => {
    if (!editingRuleSet || !newRule.rule_id || !newRule.name || !newRule.path || !newRule.message) {
      setAlert({ type: 'error', message: 'Fill in all required fields: Rule ID, Name, Path, and Message.' })
      return
    }
    const rule = {
      rule_id: newRule.rule_id,
      name: newRule.name,
      level: newRule.level.value,
      check: newRule.check.value,
      path: newRule.path,
      severity: newRule.severity.value,
      message: newRule.message,
      reference: newRule.reference || '',
    }
    if (newRule.field) rule.field = newRule.field
    if (newRule.pattern) rule.pattern = newRule.pattern
    if (newRule.note) rule.note = newRule.note

    setEditingRuleSet({
      ...editingRuleSet,
      rules: [...editingRuleSet.rules, rule]
    })
    setShowAddRuleModal(false)
    setNewRule({
      rule_id: '', name: '', level: { label: 'L3', value: 'L3' },
      check: { label: 'Field Required', value: 'field_required' },
      path: '', field: '', pattern: '',
      severity: { label: 'Error', value: 'error' },
      message: '', reference: '', note: ''
    })
  }

  const removeRule = (ruleId) => {
    setEditingRuleSet({
      ...editingRuleSet,
      rules: editingRuleSet.rules.filter(r => r.rule_id !== ruleId)
    })
  }

  // Count rules by level
  const countByLevel = (rules) => {
    const counts = { L1: 0, L2: 0, L3: 0, L4: 0 }
    rules.forEach(r => { if (counts[r.level] !== undefined) counts[r.level]++ })
    return counts
  }

  return (
    <SpaceBetween size="l">
      <Header
        variant="h1"
        description="Create, import, and manage custom validation rule sets for ASM files"
      >
        Validation Rules
      </Header>

      {alert && (
        <Alert type={alert.type} dismissible onDismiss={() => setAlert(null)}>
          {alert.message}
        </Alert>
      )}

      <Tabs
        activeTabId={activeSubTab}
        onChange={({ detail }) => setActiveSubTab(detail.activeTabId)}
        tabs={[
        {
          id: 'manage',
          label: 'Rule Set Manager',
          content: (
            <SpaceBetween size="l">
              <Container header={
                <Header variant="h2"
                  actions={
                    <SpaceBetween direction="horizontal" size="xs">
                      <Button onClick={loadTemplate}>Start from Template</Button>
                      <Button onClick={() => setShowImportModal(true)}>Import Rule Set</Button>
                    </SpaceBetween>
                  }
                >
                  Registered Rule Sets
                </Header>
              }>
                {ruleSets.length === 0 ? (
                  <Box textAlign="center" padding="l" color="inherit">
                    <Box variant="p">No rule sets registered. Start from the template or import a JSON file.</Box>
                  </Box>
                ) : (
                  <Table
                    columnDefinitions={[
                      {
                        id: 'name',
                        header: 'Rule Set',
                        cell: item => (
                          <SpaceBetween size="xxs">
                            <Box fontWeight="bold">{item.name}</Box>
                            <Box variant="small" color="text-status-inactive">{item.rule_set_id}</Box>
                          </SpaceBetween>
                        ),
                        width: 250
                      },
                      {
                        id: 'rules',
                        header: 'Rules',
                        cell: item => {
                          const counts = countByLevel(item.rules)
                          return (
                            <SpaceBetween direction="horizontal" size="xxs">
                              {Object.entries(counts).filter(([,v]) => v > 0).map(([level, count]) => (
                                <Badge key={level} color={LEVEL_COLORS[level]}>{level}: {count}</Badge>
                              ))}
                            </SpaceBetween>
                          )
                        },
                        width: 250
                      },
                      {
                        id: 'enabled',
                        header: 'Enabled',
                        cell: item => (
                          <Toggle
                            checked={item.enabled}
                            onChange={() => toggleRuleSet(item.rule_set_id)}
                          />
                        ),
                        width: 100
                      },
                      {
                        id: 'actions',
                        header: 'Actions',
                        cell: item => (
                          <SpaceBetween direction="horizontal" size="xs">
                            <Button variant="link" onClick={() => {
                      setEditingRuleSet(JSON.parse(JSON.stringify(item)))
                      setActiveSubTab('builder')
                    }}>Edit</Button>
                            <Button variant="link" onClick={() => downloadRuleSet(item)}>Download</Button>
                            <Button variant="link" onClick={() => deleteRuleSet(item.rule_set_id)}>Delete</Button>
                          </SpaceBetween>
                        )
                      }
                    ]}
                    items={ruleSets}
                  />
                )}
              </Container>

              <Alert type="info" header="How Validation Rules Work">
                <SpaceBetween size="xs">
                  <div>Core validation (JSON Schema + Data Integrity) always runs automatically.</div>
                  <div>Plugin rule sets add additional checks on top of core validation.</div>
                  <div>Enable or disable rule sets to control which checks apply to your validations.</div>
                  <div>Each finding in the validation report is tagged with the rule set and level that caught it.</div>
                  <div><strong>About Level 2:</strong> L2 (Data Integrity Verification) is not part of rule sets because it compares source instrument values against ASM values field-by-field via the converter's field_mapping. It runs automatically during conversion on the Convert Instrument File tab. Rule sets cover L1 (schema), L3 (Allotrope principles), and L4 (organization-specific) checks that validate the ASM file on its own.</div>
                </SpaceBetween>
              </Alert>
            </SpaceBetween>
          )
        },
        {
          id: 'builder',
          label: 'Rule Set Builder',
          content: (
            <SpaceBetween size="l">
              {!editingRuleSet ? (
                <Container>
                  <Box textAlign="center" padding="l">
                    <SpaceBetween size="m">
                      <Box variant="h3">No rule set loaded</Box>
                      <Box>Start from the template or import an existing rule set to begin editing.</Box>
                      <SpaceBetween direction="horizontal" size="xs">
                        <Button variant="primary" onClick={loadTemplate}>Start from Template (22 rules)</Button>
                        <Button onClick={() => setShowImportModal(true)}>Import JSON File</Button>
                        <Button onClick={() => setEditingRuleSet({
                          rule_set_id: `custom-rules-${Date.now()}`,
                          name: '',
                          version: '1.0',
                          description: '',
                          author: '',
                          rules: []
                        })}>Start Empty</Button>
                      </SpaceBetween>
                    </SpaceBetween>
                  </Box>
                </Container>
              ) : (
                <SpaceBetween size="l">
                  {/* Rule Set Metadata */}
                  <Container header={
                    <Header variant="h2"
                      actions={
                        <SpaceBetween direction="horizontal" size="xs">
                          <Button onClick={saveRuleSet} variant="primary">Save Rule Set</Button>
                          <Button onClick={() => downloadRuleSet(editingRuleSet)}>Download JSON</Button>
                        </SpaceBetween>
                      }
                    >
                      Rule Set Details
                    </Header>
                  }>
                    <ColumnLayout columns={2}>
                      <FormField label="Rule Set ID">
                        <Input
                          value={editingRuleSet.rule_set_id}
                          onChange={({ detail }) => setEditingRuleSet({ ...editingRuleSet, rule_set_id: detail.value })}
                          placeholder="my-org-rules-v1"
                        />
                      </FormField>
                      <FormField label="Name">
                        <Input
                          value={editingRuleSet.name}
                          onChange={({ detail }) => setEditingRuleSet({ ...editingRuleSet, name: detail.value })}
                          placeholder="My Organization Validation Rules"
                        />
                      </FormField>
                      <FormField label="Author">
                        <Input
                          value={editingRuleSet.author || ''}
                          onChange={({ detail }) => setEditingRuleSet({ ...editingRuleSet, author: detail.value })}
                          placeholder="Your name or organization"
                        />
                      </FormField>
                      <FormField label="Version">
                        <Input
                          value={editingRuleSet.version || '1.0'}
                          onChange={({ detail }) => setEditingRuleSet({ ...editingRuleSet, version: detail.value })}
                        />
                      </FormField>
                    </ColumnLayout>
                    <FormField label="Description">
                      <Textarea
                        value={editingRuleSet.description || ''}
                        onChange={({ detail }) => setEditingRuleSet({ ...editingRuleSet, description: detail.value })}
                        placeholder="Describe what this rule set validates"
                        rows={2}
                      />
                    </FormField>
                  </Container>

                  {/* Rules Summary */}
                  <Container header={
                    <Header variant="h2"
                      counter={`(${editingRuleSet.rules.length} rules)`}
                      actions={
                        <Button onClick={() => setShowAddRuleModal(true)}>Add Rule</Button>
                      }
                    >
                      Rules
                    </Header>
                  }>
                    {editingRuleSet.rules.length === 0 ? (
                      <Box textAlign="center" padding="l">
                        <Box variant="p">No rules yet. Click "Add Rule" to create one.</Box>
                      </Box>
                    ) : (
                      <Table
                        columnDefinitions={[
                          {
                            id: 'rule_id',
                            header: 'Rule ID',
                            cell: item => <Box fontWeight="bold">{item.rule_id}</Box>,
                            width: 120
                          },
                          {
                            id: 'level',
                            header: 'Level',
                            cell: item => <Badge color={LEVEL_COLORS[item.level] || 'grey'}>{item.level}</Badge>,
                            width: 80
                          },
                          {
                            id: 'name',
                            header: 'Name',
                            cell: item => item.name,
                            width: 200
                          },
                          {
                            id: 'check',
                            header: 'Check Type',
                            cell: item => item.check,
                            width: 150
                          },
                          {
                            id: 'severity',
                            header: 'Severity',
                            cell: item => (
                              <StatusIndicator type={item.severity === 'error' ? 'error' : item.severity === 'warning' ? 'warning' : 'info'}>
                                {item.severity}
                              </StatusIndicator>
                            ),
                            width: 100
                          },
                          {
                            id: 'actions',
                            header: 'Actions',
                            cell: item => (
                              <Button variant="link" onClick={() => removeRule(item.rule_id)}>Remove</Button>
                            ),
                            width: 80
                          }
                        ]}
                        items={editingRuleSet.rules}
                      />
                    )}
                  </Container>

                  {/* JSON Preview */}
                  <ExpandableSection headerText="JSON Preview" variant="container">
                    <pre style={{
                      background: '#232f3e', color: '#d5dbdb', padding: '16px',
                      borderRadius: '4px', overflow: 'auto', fontSize: '12px', maxHeight: '400px'
                    }}>
                      {JSON.stringify(editingRuleSet, null, 2)}
                    </pre>
                  </ExpandableSection>
                </SpaceBetween>
              )}
            </SpaceBetween>
          )
        }
      ]} />

      {/* Import Modal */}
      <Modal
        visible={showImportModal}
        onDismiss={() => { setShowImportModal(false); setImportFile([]) }}
        header="Import Rule Set"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button variant="link" onClick={() => { setShowImportModal(false); setImportFile([]) }}>Cancel</Button>
              <Button variant="primary" onClick={importRuleSet} disabled={!importFile.length}>Import</Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="m">
          <FormField label="Rule Set File" description="Upload a JSON rule set file">
            <FileUpload
              value={importFile}
              onChange={({ detail }) => setImportFile(detail.value)}
              accept=".json"
              i18nStrings={{
                uploadButtonText: e => e ? "Choose files" : "Choose file",
                dropzoneText: e => e ? "Drop files to upload" : "Drop file to upload",
                removeFileAriaLabel: e => `Remove file ${e + 1}`,
                limitShowFewer: "Show fewer files",
                limitShowMore: "Show more files",
                errorIconAriaLabel: "Error"
              }}
              showFileSize
              tokenLimit={1}
            />
          </FormField>
          <Alert type="info">
            The JSON file must contain a <code>rule_set_id</code> and a <code>rules</code> array.
            You can download the template first, customize it, and import it back.
          </Alert>
        </SpaceBetween>
      </Modal>

      {/* Add Rule Modal */}
      <Modal
        visible={showAddRuleModal}
        onDismiss={() => setShowAddRuleModal(false)}
        header="Add Validation Rule"
        size="large"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button variant="link" onClick={() => setShowAddRuleModal(false)}>Cancel</Button>
              <Button variant="primary" onClick={addRule}
                disabled={!newRule.rule_id || !newRule.name || !newRule.path || !newRule.message}
              >Add Rule</Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="m">
          <ColumnLayout columns={2}>
            <FormField label="Rule ID" constraintText="Required — unique identifier">
              <Input value={newRule.rule_id} onChange={({ detail }) => setNewRule({ ...newRule, rule_id: detail.value })}
                placeholder="L3-014" />
            </FormField>
            <FormField label="Name" constraintText="Required">
              <Input value={newRule.name} onChange={({ detail }) => setNewRule({ ...newRule, name: detail.value })}
                placeholder="My custom check" />
            </FormField>
          </ColumnLayout>

          <ColumnLayout columns={3}>
            <FormField label="Level">
              <Select selectedOption={newRule.level}
                onChange={({ detail }) => setNewRule({ ...newRule, level: detail.selectedOption })}
                options={[
                  { label: 'L1 — Schema', value: 'L1' },
                  { label: 'L3 — Allotrope Principles', value: 'L3' },
                  { label: 'L4 — Organization-Specific', value: 'L4' },
                ]}
              />
            </FormField>
            <FormField label="Check Type">
              <Select selectedOption={newRule.check}
                onChange={({ detail }) => setNewRule({ ...newRule, check: detail.selectedOption })}
                options={CHECK_TYPES}
              />
            </FormField>
            <FormField label="Severity">
              <Select selectedOption={newRule.severity}
                onChange={({ detail }) => setNewRule({ ...newRule, severity: detail.selectedOption })}
                options={[
                  { label: 'Error', value: 'error' },
                  { label: 'Warning', value: 'warning' },
                  { label: 'Info', value: 'info' },
                ]}
              />
            </FormField>
          </ColumnLayout>

          <FormField label="JSON Path" constraintText="Required — use ** for recursive, [*] for arrays"
            description="Path to the field to check in the ASM document">
            <Input value={newRule.path} onChange={({ detail }) => setNewRule({ ...newRule, path: detail.value })}
              placeholder="**.measurement document[*]" />
          </FormField>

          {(newRule.check.value === 'field_required' || newRule.check.value === 'field_not_empty') && (
            <FormField label="Field Name" description="The field that must exist or not be empty">
              <Input value={newRule.field} onChange={({ detail }) => setNewRule({ ...newRule, field: detail.value })}
                placeholder="analyst" />
            </FormField>
          )}

          {(newRule.check.value === 'value_matches_pattern' || newRule.check.value === 'key_not_matches_pattern') && (
            <FormField label="Regex Pattern" description="Regular expression to match against">
              <Input value={newRule.pattern} onChange={({ detail }) => setNewRule({ ...newRule, pattern: detail.value })}
                placeholder="^[0-9a-f]{8}-..." />
            </FormField>
          )}

          <FormField label="Error Message" constraintText="Required — shown when the check fails">
            <Textarea value={newRule.message} onChange={({ detail }) => setNewRule({ ...newRule, message: detail.value })}
              placeholder="The 'analyst' field is required in each technique document" rows={2} />
          </FormField>

          <FormField label="Reference (Optional)" description="Document or standard this rule comes from">
            <Input value={newRule.reference} onChange={({ detail }) => setNewRule({ ...newRule, reference: detail.value })}
              placeholder="ASM Building Principles - Section X" />
          </FormField>
        </SpaceBetween>
      </Modal>
    </SpaceBetween>
  )
}

export default ValidationRulesApp
