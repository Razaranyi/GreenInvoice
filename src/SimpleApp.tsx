import React from 'react';

function SimpleApp() {
  return (
    <div style={{ padding: '20px', textAlign: 'center' }}>
      <h1>Green Invoice Automation</h1>
      <button 
        style={{ 
          padding: '10px 20px', 
          backgroundColor: '#00a8ff', 
          color: 'white', 
          border: 'none', 
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        Click Me
      </button>
    </div>
  );
}

export default SimpleApp; 