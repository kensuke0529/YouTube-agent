import React from 'react'

export default function App() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>YouTube Learning AI - Test</h1>
      <p>If you can see this, the React app is working!</p>
      <p>Environment: {import.meta.env.MODE}</p>
      <p>API Base: {import.meta.env.VITE_API_BASE || 'Not set'}</p>
    </div>
  )
}
