import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AppDataProvider } from './app/AppDataProvider'
import { OwnerLayout } from './components/OwnerLayout'
import { BeneficiaryPage } from './pages/BeneficiaryPage'
import { BeneficiariesPage } from './pages/BeneficiariesPage'
import { DashboardPage } from './pages/DashboardPage'
import { EntryDetailPage } from './pages/EntryDetailPage'
import { EntriesPage } from './pages/EntriesPage'
import { EntryEditorPage } from './pages/EntryEditorPage'
import { IntroPage } from './pages/IntroPage'
import { LoginPage } from './pages/LoginPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { PolicyPage } from './pages/PolicyPage'
import { QAPage } from './pages/QAPage'
import { SettingsPage } from './pages/SettingsPage'
import './App.css'

function App() {
  return (
    <BrowserRouter>
      <AppDataProvider>
        <Routes>
          <Route path="/" element={<IntroPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/beneficiary" element={<BeneficiaryPage />} />
          <Route path="/owner" element={<OwnerLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="entries" element={<EntriesPage />} />
            <Route path="entries/new" element={<EntryEditorPage />} />
            <Route path="entries/:entryId" element={<EntryDetailPage />} />
            <Route path="beneficiaries" element={<BeneficiariesPage />} />
            <Route path="policy" element={<PolicyPage />} />
            <Route path="ask" element={<QAPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AppDataProvider>
    </BrowserRouter>
  )
}

export default App
