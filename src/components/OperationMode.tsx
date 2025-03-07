import React from 'react';
import { Box, RadioGroup, FormControlLabel, Radio, FormControl, Typography } from '@mui/material';

interface OperationModeProps {
  onOperationSelect: (operation: string) => void;
  selectedOperation: string | null;
}

const operations = [
  {
    value: 'checkClient',
    label: 'Check Client',
    description: 'Verify if clients exist in the system'
  },
  {
    value: 'preview',
    label: 'Preview Invoice',
    description: 'Generate a preview of the invoice'
  },
  {
    value: 'generate',
    label: 'Generate Invoice',
    description: 'Create and save the invoice'
  }
];

function OperationMode({ onOperationSelect, selectedOperation }: OperationModeProps) {
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    onOperationSelect(event.target.value);
  };

  return (
    <Box sx={{ py: 2 }}>
      <FormControl component="fieldset">
        <RadioGroup
          value={selectedOperation || ''}
          onChange={handleChange}
        >
          {operations.map((operation) => (
            <Box
              key={operation.value}
              sx={{
                mb: 2,
                p: 2,
                border: '1px solid',
                borderColor: selectedOperation === operation.value ? 'primary.main' : 'divider',
                borderRadius: 2,
                '&:hover': {
                  bgcolor: 'action.hover',
                }
              }}
            >
              <FormControlLabel
                value={operation.value}
                control={<Radio />}
                label={
                  <Box>
                    <Typography variant="subtitle1" component="div">
                      {operation.label}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {operation.description}
                    </Typography>
                  </Box>
                }
                sx={{ m: 0, width: '100%' }}
              />
            </Box>
          ))}
        </RadioGroup>
      </FormControl>
    </Box>
  );
}

export default OperationMode; 