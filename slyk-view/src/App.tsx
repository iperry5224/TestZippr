import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import Controls from './pages/Controls'
import Chat from './pages/Chat'
import Inventory from './pages/Inventory'
import Reports from './pages/Reports'
import Settings from './pages/Settings'
import { TenantProvider } from './context/TenantContext'
import { AuthProvider } from './context/AuthContext'

function App() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <AuthProvider>
      <TenantProvider>
        <BrowserRouter>
          <div className="flex h-screen overflow-hidden">
            <Sidebar 
              collapsed={sidebarCollapsed} 
              onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} 
            />
            <main className={`flex-1 overflow-auto transition-all duration-300 ${sidebarCollapsed ? 'ml-20' : 'ml-64'}`}>
              <AnimatePresence mode="wait">
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/controls" element={<Controls />} />
                  <Route path="/controls/:controlId" element={<Controls />} />
                  <Route path="/chat" element={<Chat />} />
                  <Route path="/inventory" element={<Inventory />} />
                  <Route path="/reports" element={<Reports />} />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </AnimatePresence>
            </main>
          </div>
        </BrowserRouter>
      </TenantProvider>
    </AuthProvider>
  )
}

export default App
