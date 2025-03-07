import React, { useState, useRef } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { open } from '@tauri-apps/plugin-dialog';
import './styles.css';

// Add CSS keyframes for the progress bar animation
const progressBarStyles = `
  @keyframes progress {
    0% {
      background-position: 200% 0;
    }
    100% {
      background-position: -200% 0;
    }
  }
`;

// Define the result interface
interface InvoiceResult {
  success: boolean;
  message: string;
  missing_clients?: string[];
}

function App() {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [selectedOperation, setSelectedOperation] = useState<string | null>(null);
  const [result, setResult] = useState<InvoiceResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showMissingClientsDialog, setShowMissingClientsDialog] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const operations = [
    { value: 'checkClient', label: 'Check Client' },
    { value: 'preview', label: 'Preview Invoice' },
    { value: 'generate', label: 'Generate Invoice' }
  ];

  const handleFileSelect = async () => {
    try {
      const selected = await open({
        multiple: false,
        filters: [{
          name: 'Excel',
          extensions: ['xlsx', 'xls']
        }]
      });
      if (selected === null) {
        // User cancelled the selection
        return;
      }
      if (Array.isArray(selected)) {
        setSelectedFile(selected[0]);
      } else {
        setSelectedFile(selected);
      }
    } catch (error) {
      console.error('Error selecting file:', error);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    // This is now just a fallback, we primarily use the Tauri dialog
    const files = event.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      setSelectedFile(file.name);
    }
  };

  const handleOperationSelect = (operation: string) => {
    setSelectedOperation(operation);
  };

  const handleProcess = async () => {
    if (!selectedFile || !selectedOperation) return;

    setIsProcessing(true);
    
    try {
      // Make a real call to the Tauri backend
      const result = await invoke<InvoiceResult>('run_invoice_command', {
        filePath: selectedFile,
        operation: selectedOperation,
      });
      
      setResult(result);
      
      // Show dialog to add missing clients if any were found
      if (result.missing_clients && result.missing_clients.length > 0) {
        setShowMissingClientsDialog(true);
      }
    } catch (error) {
      console.error('Error processing request:', error);
      setResult({
        success: false,
        message: `Error: ${error}`,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleAddMissingClients = async () => {
    if (!result?.missing_clients) return;
    
    setIsProcessing(true);
    
    try {
      // Make a real call to the Tauri backend to add missing clients
      const addResult = await invoke<InvoiceResult>('add_missing_clients', {
        clients: result.missing_clients,
      });
      
      setResult(addResult);
      setShowMissingClientsDialog(false);
    } catch (error) {
      console.error('Error adding clients:', error);
      setResult({
        success: false,
        message: `Error adding clients: ${error}`,
      });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <>
      <style>{progressBarStyles}</style>
      <div style={{ 
        padding: '20px', 
        maxWidth: '800px', 
        margin: '0 auto',
        backgroundColor: '#2d2d2d',
        color: 'white',
        borderRadius: '12px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
      }}>
        <h1 style={{ textAlign: 'center', marginBottom: '30px' }}>Green Invoice Automation</h1>
        
        {/* Hidden file input */}
        <input 
          type="file" 
          ref={fileInputRef} 
          style={{ display: 'none' }} 
          accept=".xlsx,.xls" 
          onChange={handleFileChange}
        />
        
        <div style={{ marginBottom: '20px' }}>
          <h2>Step 1: Select File</h2>
          <button 
            onClick={handleFileSelect}
            style={{
              padding: '10px 20px',
              backgroundColor: '#00a8ff',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              marginRight: '10px'
            }}
          >
            Select Excel File
          </button>
          {selectedFile && (
            <span>Selected: {selectedFile.split('/').pop()}</span>
          )}
        </div>
        
        <div style={{ marginBottom: '20px' }}>
          <h2>Step 2: Choose Operation</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {operations.map(op => (
              <div 
                key={op.value}
                onClick={() => handleOperationSelect(op.value)}
                style={{
                  padding: '10px',
                  border: `1px solid ${selectedOperation === op.value ? '#00a8ff' : '#555'}`,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  backgroundColor: selectedOperation === op.value ? 'rgba(0, 168, 255, 0.1)' : 'transparent'
                }}
              >
                {op.label}
              </div>
            ))}
          </div>
        </div>
        
        <div style={{ marginBottom: '20px' }}>
          <h2>Step 3: Process</h2>
          <button 
            onClick={handleProcess}
            disabled={!selectedFile || !selectedOperation || isProcessing}
            style={{
              padding: '10px 20px',
              backgroundColor: (!selectedFile || !selectedOperation || isProcessing) ? '#555' : '#00a8ff',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: (!selectedFile || !selectedOperation || isProcessing) ? 'not-allowed' : 'pointer',
            }}
          >
            {isProcessing ? 'Processing...' : 'Process'}
          </button>
        </div>
        
        {isProcessing && (
          <div className="progress-container">
            <div className="progress-content">
              <div className="progress-bar">
                <div className="progress-bar-fill"></div>
              </div>
              <p className="progress-text">Processing your request...</p>
            </div>
          </div>
        )}
        
        {result && !isProcessing && !showMissingClientsDialog && (
          <div style={{ 
            marginTop: '20px', 
            padding: '15px', 
            backgroundColor: result.success ? '#4CAF50' : '#f44336', 
            borderRadius: '8px' 
          }}>
            <p>{result.message}</p>
          </div>
        )}
        
        {/* Missing Clients Dialog */}
        {showMissingClientsDialog && result?.missing_clients && (
          <div style={{
            marginTop: '20px',
            padding: '20px',
            backgroundColor: '#333',
            borderRadius: '8px',
            border: '1px solid #555'
          }}>
            <h3>Missing Clients Found</h3>
            <p>The following clients are missing in the system:</p>
            <ul style={{ marginBottom: '20px' }}>
              {result.missing_clients.map((client, index) => (
                <li key={index}>{client}</li>
              ))}
            </ul>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
              <button
                onClick={() => setShowMissingClientsDialog(false)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#555',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleAddMissingClients}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#00a8ff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Add Clients
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

export default App; 