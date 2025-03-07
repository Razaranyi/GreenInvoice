import React from 'react';
import { Box, Button, Typography } from '@mui/material';
import { UploadFile } from '@mui/icons-material';
import { open } from '@tauri-apps/api/dialog';

interface FileSelectionProps {
  onFileSelect: (file: string) => void;
  selectedFile: string | null;
}

function FileSelection({ onFileSelect, selectedFile }: FileSelectionProps) {
  const handleFileSelect = async () => {
    try {
      const selected = await open({
        multiple: false,
        filters: [{
          name: 'Excel',
          extensions: ['xlsx', 'xls']
        }]
      });

      if (selected && typeof selected === 'string') {
        onFileSelect(selected);
      }
    } catch (error) {
      console.error('Error selecting file:', error);
    }
  };

  return (
    <Box sx={{ textAlign: 'center', py: 3 }}>
      <Button
        variant="outlined"
        startIcon={<UploadFile />}
        onClick={handleFileSelect}
        sx={{
          mb: 2,
          p: 2,
          minWidth: 200,
          borderStyle: 'dashed',
          borderWidth: 2,
        }}
      >
        Select Excel File
      </Button>
      {selectedFile && (
        <Typography variant="body1" color="text.secondary">
          Selected: {selectedFile.split('/').pop()}
        </Typography>
      )}
    </Box>
  );
}

export default FileSelection; 