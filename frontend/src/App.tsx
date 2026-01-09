import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { PrivacyProvider } from './context/PrivacyContext';
import Dashboard from './pages/Dashboard';
import RiskAnalysis from './pages/RiskAnalysis';
import AICopilot from './pages/AICopilot';
import Settings from './pages/Settings';

function App() {
  return (
    <PrivacyProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/risk" element={<RiskAnalysis />} />
          <Route path="/ai" element={<AICopilot />} />
          <Route path="/settings" element={<Settings />} />
          {/* 其他路由暫時導向首頁 */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </PrivacyProvider>
  );
}

export default App;
