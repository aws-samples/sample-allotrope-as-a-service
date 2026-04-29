// Copyright 2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
// Licensed under the Apache License, Version 2.0 (the "License").
// You may not use this file except in compliance with the License.
// A copy of the License is located at http://aws.amazon.com/apache2.0/
// This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
import React, { useState } from 'react';
import {
  Container,
  Header,
  SpaceBetween,
  Button,
  Table,
  Box,
  Badge,
  Modal,
  FormField,
  Input,
  Select,
  Alert,
  FileUpload,
  Textarea,
  StatusIndicator
} from '@cloudscape-design/components';

import { ENDPOINTS, authFetch } from './config';

const CUSTOM_CONVERTER_API = ENDPOINTS.customConverter;

export default function ConverterManagementApp() {
  const [converters, setConverters] = useState([]);
  const [selectedConverter, setSelectedConverter] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState(null);

  // Registration form state
  const [vendor, setVendor] = useState('');
  const [model, setModel] = useState('');

  const generateConverterId = (v, m) => {
    if (!v || !m) return '';
    const base = `${v}-${m}`.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
    const existing = converters.filter(c => c.converter_id && c.converter_id.startsWith(base + '-v'));
    const maxVersion = existing.reduce((max, c) => {
      const match = c.converter_id.match(/-v(\d+)$/);
      return match ? Math.max(max, parseInt(match[1])) : max;
    }, 0);
    return `${base}-v${maxVersion + 1}`;
  };

  const converterId = generateConverterId(vendor, model);
  const [instrumentType, setInstrumentType] = useState({ value: 'solution_analyzer' });
  const [description, setDescription] = useState('');
  const [converterFile, setConverterFile] = useState([]);
  const [validationErrors, setValidationErrors] = useState([]);
  const [validationWarnings, setValidationWarnings] = useState([]);
  
  // Approval form state
  const [approvalComments, setApprovalComments] = useState('');
  const [approvalDecision, setApprovalDecision] = useState('approve');
  const [reviewerEmail, setReviewerEmail] = useState('');

  const loadConverters = async () => {
    setLoading(true);
    try {
      const response = await authFetch(`${CUSTOM_CONVERTER_API}/list`);
      if (!response.ok) throw new Error('Failed to load converters');
      
      const data = await response.json();
      setConverters(data.converters || []);
    } catch (error) {
      setAlert({ type: 'error', message: `Failed to load converters: ${error.message}` });
    }
    setLoading(false);
  };

  const validateConverter = async (file) => {
    const errors = [];
    const warnings = [];
    
    if (!file.name.endsWith('.py')) {
      errors.push('Converter must be a Python (.py) file');
    }
    
    if (file.size > 1024 * 1024) {
      errors.push('File size must be less than 1MB');
    }

    try {
      const content = await file.text();
      
      // Check for convert function
      if (!content.includes('def convert')) {
        errors.push('Converter must contain a "convert" function');
      } else {
        // Check function signature
        const convertMatch = content.match(/def convert\s*\(([^)]*)\)/);
        if (convertMatch) {
          const params = convertMatch[1];
          if (params.includes('input_path') || params.includes('output_path')) {
            errors.push('CLI-style signature detected (input_path/output_path). Must use convert(file_content) — see Custom Converter Requirements');
          }
          if (!params.includes('content') && !params.includes('data') && !params.includes('text')) {
            warnings.push('Function should accept file content as parameter (e.g., file_content, data, text)');
          }
        }
      }
      
      // Security: dangerous functions
      const dangerousPatterns = ['eval(', 'exec(', '__import__', 'os.system', 'subprocess'];
      for (const pattern of dangerousPatterns) {
        if (content.includes(pattern)) {
          errors.push(`Security risk: Code contains ${pattern}`);
        }
      }

      // Security: filesystem access
      // const fsPatterns = ["open(", "Path(", "os.path", ".read_text", ".write_text", ".read_bytes", ".write_bytes"];
      // for (const pattern of fsPatterns) {
      //   if (content.includes(pattern)) {
      //     errors.push(`Filesystem access not allowed: Code contains ${pattern} — converter must use file_content string parameter, not read files directly`);
      //     break;
      //   }
      // }

      // Security: network calls
      const netPatterns = ["requests.", "urllib", "http.client", "socket."];
      for (const pattern of netPatterns) {
        if (content.includes(pattern)) {
          errors.push(`Network access not allowed: Code contains ${pattern}`);
          break;
        }
      }

      // Return format: check for success/asm_output/field_mapping
      if (!content.includes('success')) {
        warnings.push('Return format should include "success" key (True/False) — see Custom Converter Requirements');
      }
      if (!content.includes('asm_output')) {
        warnings.push('Return format should include "asm_output" key with the ASM JSON — see Custom Converter Requirements');
      }
      if (!content.includes('field_mapping')) {
        warnings.push('Return format should include "field_mapping" array for Data Integrity Verification — see Custom Converter Requirements');
      }

      // ASM structure: check for manifest
      if (!content.includes('asm.manifest')) {
        warnings.push('ASM output should include "$asm.manifest" with the Allotrope manifest URL');
      }

      // Best practices: UUID for measurement identifiers
      if (!content.includes('uuid')) {
        warnings.push('Measurement identifiers should use UUID v4 — consider importing uuid module');
      }

    } catch (err) {
      errors.push('Unable to read file content');
    }

    return { errors, warnings };
  };

  const registerConverter = async () => {
    if (!converterFile.length || !vendor || !model) {
      setAlert({ type: 'error', message: 'Please fill in all required fields and upload a file' });
      return;
    }

    setLoading(true);
    setValidationErrors([]);
    setValidationWarnings([]);

    try {
      // Validate converter code
      const { errors, warnings } = await validateConverter(converterFile[0]);
      
      setValidationWarnings(warnings);
      
      if (errors.length > 0) {
        setValidationErrors(errors);
        setLoading(false);
        return;
      }

      // Read file content
      const fileContent = await converterFile[0].text();

      const response = await authFetch(`${CUSTOM_CONVERTER_API}/register`, {
        method: 'POST',
        body: JSON.stringify({
          converter_id: converterId,
          converter_code: fileContent,
          vendor: vendor,
          model: model,
          instrument_type: instrumentType.value,
          description: description,
          filename: converterFile[0].name
        })
      });

      if (!response.ok) throw new Error('Registration failed');

      const result = await response.json();
      setAlert({ type: 'success', message: `Converter registered! Approval ID: ${result.converter_id}` });
      setShowRegisterModal(false);
      
      // Reset form
      setVendor('');
      setModel('');
      setDescription('');
      setConverterFile([]);
      
      loadConverters();
    } catch (error) {
      setAlert({ type: 'error', message: `Registration failed: ${error.message}` });
    }
    setLoading(false);
  };

  const approveConverter = async (decision) => {
    setLoading(true);
    try {
      // Use /approve endpoint for both approve and reject
      // Backend should handle status field
      const response = await authFetch(`${CUSTOM_CONVERTER_API}/approve`, {
        method: 'POST',
        body: JSON.stringify({
          converter_id: selectedConverter.converter_id,
          approved_by: reviewerEmail,
          comments: approvalComments,
          status: decision === 'approve' ? 'APPROVED' : 'REJECTED'
        })
      });

      if (!response.ok) throw new Error(`${decision} failed`);

      const result = await response.json();
      setAlert({ 
        type: 'success', 
        message: `Converter ${decision === 'approve' ? 'approved' : 'rejected'}!` 
      });
      setShowApprovalModal(false);
      setApprovalComments('');
      setReviewerEmail('');
      loadConverters();
    } catch (error) {
      setAlert({ type: 'error', message: `Action failed: ${error.message}` });
    }
    setLoading(false);
  };

  React.useEffect(() => {
    loadConverters();
  }, []);

  return (
    <SpaceBetween size="l">
      {alert && (
        <Alert
          type={alert.type}
          dismissible
          onDismiss={() => setAlert(null)}
        >
          {alert.message}
        </Alert>
      )}

      <Container
        header={
          <Header
            variant="h2"
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Button onClick={loadConverters} loading={loading}>Refresh</Button>
                <Button variant="primary" onClick={() => setShowRegisterModal(true)}>
                  Register New Converter
                </Button>
              </SpaceBetween>
            }
          >
            Custom Converter Registry
          </Header>
        }
      >
        <Table
          columnDefinitions={[
            {
              id: 'converter_id',
              header: 'Converter ID',
              cell: item => item.converter_id
            },
            {
              id: 'vendor',
              header: 'Vendor',
              cell: item => item.vendor
            },
            {
              id: 'model',
              header: 'Model',
              cell: item => item.model
            },
            {
              id: 'instrument_type',
              header: 'Type',
              cell: item => item.instrument_type
            },
            {
              id: 'status',
              header: 'Status',
              cell: item => (
                <Badge color={item.status === 'APPROVED' ? 'green' : 'grey'}>
                  {item.status}
                </Badge>
              )
            },
            {
              id: 'actions',
              header: 'Actions',
              cell: item => (
                <SpaceBetween direction="horizontal" size="xs">
                  <Button
                    variant="link"
                    onClick={() => {
                      setSelectedConverter(item);
                      setShowDetailsModal(true);
                    }}
                  >
                    View Details
                  </Button>
                  {item.status === 'PENDING' && (
                    <Button
                      variant="primary"
                      onClick={() => {
                        setSelectedConverter(item);
                        setShowApprovalModal(true);
                      }}
                      loading={loading}
                    >
                      Review
                    </Button>
                  )}
                </SpaceBetween>
              )
            }
          ]}
          items={converters}
          loading={loading}
          empty={
            <Box textAlign="center" color="inherit">
              <b>No converters</b>
              <Box padding={{ bottom: 's' }} variant="p" color="inherit">
                Register a new converter to get started.
              </Box>
            </Box>
          }
        />
      </Container>

      {/* View Details Modal */}
      <Modal
        visible={showDetailsModal}
        onDismiss={() => setShowDetailsModal(false)}
        header="Converter Details"
        size="large"
      >
        <SpaceBetween size="m">
          <Box>
            <strong>Converter ID:</strong> {selectedConverter?.converter_id}
          </Box>
          <Box>
            <strong>Vendor:</strong> {selectedConverter?.vendor}
          </Box>
          <Box>
            <strong>Model:</strong> {selectedConverter?.model}
          </Box>
          <Box>
            <strong>Instrument Type:</strong> {selectedConverter?.instrument_type}
          </Box>
          <Box>
            <strong>Status:</strong> <Badge color={selectedConverter?.status === 'APPROVED' ? 'green' : selectedConverter?.status === 'REJECTED' ? 'red' : 'grey'}>
              {selectedConverter?.status}
            </Badge>
          </Box>
          {selectedConverter?.description && (
            <Box>
              <strong>Description:</strong> {selectedConverter?.description}
            </Box>
          )}
          <Box>
            <strong>S3 Location:</strong> {selectedConverter?.s3_location || 'converters/' + selectedConverter?.converter_id + '.py'}
          </Box>
          {selectedConverter?.comments && (
            <Alert type="info" header="Review Comments">
              {selectedConverter?.comments}
            </Alert>
          )}
          <Alert type="info" header="Download Code for Review">
            To review the converter code offline:
            <ol>
              <li>Open AWS Console → S3</li>
              <li>Download: <code>{selectedConverter?.s3_location || 'converters/' + selectedConverter?.converter_id + '.py'}</code></li>
            </ol>
          </Alert>
        </SpaceBetween>
      </Modal>

      {/* Approval Modal */}
      <Modal
        visible={showApprovalModal}
        onDismiss={() => {
          setShowApprovalModal(false);
          setApprovalComments('');
        }}
        header="Review Converter"
        size="large"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button 
                variant="link" 
                onClick={() => {
                  setShowApprovalModal(false);
                  setApprovalComments('');
                }}
              >
                Cancel
              </Button>
              <Button
                onClick={() => approveConverter('reject')}
                loading={loading}
                disabled={!reviewerEmail}
              >
                Reject
              </Button>
              <Button
                variant="primary"
                onClick={() => approveConverter('approve')}
                loading={loading}
                disabled={!reviewerEmail}
              >
                Approve
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="m">
          <Alert type="info">
            Review the converter code offline before approving. Download from S3 and check for:
            <ul>
              <li>Code quality and readability</li>
              <li>Security issues (no eval, exec, os.system, etc.)</li>
              <li>ASM compliance (proper structure and fields)</li>
              <li>Error handling</li>
            </ul>
          </Alert>

          <Box>
            <strong>Converter ID:</strong> {selectedConverter?.converter_id}
          </Box>
          <Box>
            <strong>Vendor:</strong> {selectedConverter?.vendor}
          </Box>
          <Box>
            <strong>Model:</strong> {selectedConverter?.model}
          </Box>
          <Box>
            <strong>S3 Location:</strong> <code>{selectedConverter?.s3_location || 'converters/' + selectedConverter?.converter_id + '.py'}</code>
          </Box>

          <FormField
            label="Your Email"
            description="Required for audit trail — identifies who approved or rejected this converter"
            constraintText="Required"
          >
            <Input
              value={reviewerEmail}
              onChange={({ detail }) => setReviewerEmail(detail.value)}
              placeholder="reviewer@company.com"
              type="email"
            />
          </FormField>

          <FormField
            label="Review Comments"
            description="Add comments about your review (required for rejection, optional for approval)"
          >
            <Textarea
              value={approvalComments}
              onChange={({ detail }) => setApprovalComments(detail.value)}
              placeholder="e.g., Code looks good, ASM structure is correct, approved for deployment."
              rows={4}
            />
          </FormField>
        </SpaceBetween>
      </Modal>

      {/* Register Converter Modal */}
      <Modal
        visible={showRegisterModal}
        onDismiss={() => {
          setShowRegisterModal(false);
          setValidationErrors([]);
          setValidationWarnings([]);
          setAlert(null);
        }}
        header="Register New Converter"
        size="large"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button 
                variant="link" 
                onClick={() => {
                  setShowRegisterModal(false);
                  setValidationErrors([]);
                  setValidationWarnings([]);
                  setAlert(null);
                }}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={registerConverter}
                loading={loading}
                disabled={!vendor || !model || !converterFile.length}
              >
                Upload for Approval
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        <SpaceBetween size="m">
          <Alert type="info">
            Upload your Python converter code. It will be validated, uploaded to S3, and submitted for human review.
          </Alert>

          {converterId && (
            <Alert type="info">
              Converter ID: <strong>{converterId}</strong>
            </Alert>
          )}

          <FormField 
            label="Vendor" 
            description="Vendor identifier (e.g., NOVABIO_FLEX2)"
            constraintText="Required"
          >
            <Input
              value={vendor}
              onChange={e => setVendor(e.detail.value)}
              placeholder="VENDOR_NAME"
            />
          </FormField>

          <FormField 
            label="Model" 
            description="Instrument model"
            constraintText="Required"
          >
            <Input
              value={model}
              onChange={e => setModel(e.detail.value)}
              placeholder="Model Name"
            />
          </FormField>

          <FormField label="Instrument Type">
            <Select
              selectedOption={instrumentType}
              onChange={e => setInstrumentType(e.detail.selectedOption)}
              options={[
                { value: 'solution_analyzer', label: 'Solution Analyzer' },
                { value: 'plate_reader', label: 'Plate Reader' },
                { value: 'cell_counter', label: 'Cell Counter' },
                { value: 'spectrophotometer', label: 'Spectrophotometer' },
                { value: 'chromatography', label: 'Chromatography' },
                { value: 'qpcr', label: 'qPCR' },
                { value: 'dpcr', label: 'dPCR' },
                { value: 'endotoxin_testing', label: 'Endotoxin Testing' },
                { value: 'electrophoresis', label: 'Electrophoresis' },
                { value: 'light_obscuration', label: 'Light Obscuration' }
              ]}
              filteringType="auto"
              placeholder="Select or type instrument type"
              empty="No match found — type your own"
            />
          </FormField>

          <FormField 
            label="Description" 
            description="Brief description of what this converter does"
          >
            <Textarea
              value={description}
              onChange={({ detail }) => setDescription(detail.value)}
              placeholder="e.g., Converts Nova FLEX2 CSV files to ASM solution analyzer format"
              rows={2}
            />
          </FormField>

          <FormField
            label="Converter File"
            description="Upload your Python converter code (.py file)"
            constraintText="Required - Must be .py file, max 1MB"
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

          {validationWarnings.length > 0 && (
            <Alert type="warning" header="Validation Warnings">
              <ul>
                {validationWarnings.map((warning, index) => (
                  <li key={index}>{warning}</li>
                ))}
              </ul>
              <Box margin={{ top: 's' }}>
                <strong>Note:</strong> Warnings don't block upload, but the reviewer will check these issues.
              </Box>
            </Alert>
          )}

          <Alert type="warning" header="What Happens Next">
            <ol>
              <li><StatusIndicator type="info">Validation</StatusIndicator> - Code is checked for security issues</li>
              <li><StatusIndicator type="info">Upload to S3</StatusIndicator> - Code is stored securely</li>
              <li><StatusIndicator type="info">Human Review</StatusIndicator> - Reviewer examines code offline</li>
              <li><StatusIndicator type="info">Approval/Rejection</StatusIndicator> - Reviewer approves or rejects with comments</li>
              <li><StatusIndicator type="success">Deployment</StatusIndicator> - Approved converters are deployed</li>
            </ol>
          </Alert>
        </SpaceBetween>
      </Modal>
    </SpaceBetween>
  );
}
