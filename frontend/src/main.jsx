import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { ArglyProvider } from './context/ArglyContext'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ArglyProvider>
      <App />
    </ArglyProvider>
  </StrictMode>,
)
