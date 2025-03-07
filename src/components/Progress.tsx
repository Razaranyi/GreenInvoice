import React from 'react';
import { Box, CircularProgress, Typography, Paper } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

interface InvoiceResult {
  success: boolean;
  message: string;
}

interface ProgressProps {
  isProcessing: boolean;
  result: InvoiceResult | null;
}

function Progress({ isProcessing, result }: ProgressProps) {
  return (
    <Box sx={{ textAlign: 'center', py: 4 }}>
      {isProcessing ? (
        <>
          <CircularProgress size={60} thickness={4} sx={{ mb: 2 }} />
          <Typography variant="h6">
            Processing...
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Please wait while we process your request
          </Typography>
        </>
      ) : result ? (
        <Paper 
          elevation={0} 
          sx={{ 
            p: 3, 
            bgcolor: result.success ? 'success.light' : 'error.light',
            color: 'white',
            borderRadius: 2
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mb: 2 }}>
            {result.success ? (
              <CheckCircleIcon sx={{ fontSize: 40, mr: 1 }} />
            ) : (
              <ErrorIcon sx={{ fontSize: 40, mr: 1 }} />
            )}
            <Typography variant="h6">
              {result.success ? 'Success!' : 'Error'}
            </Typography>
          </Box>
          <Typography variant="body1">
            {result.message}
          </Typography>
        </Paper>
      ) : (
        <Typography variant="h6">
          Ready to process
        </Typography>
      )}
    </Box>
  );
}

export default Progress; 