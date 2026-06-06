import { AppProvider, useApp } from './context/AppContext'
import UploadPage from './pages/Home'
import QuestionsPage from './pages/Analysis'
import ResultPage from './pages/Results'

function Pages() {
  const { step } = useApp()
  if (step === 'questions') return <QuestionsPage />
  if (step === 'result')    return <ResultPage />
  return <UploadPage />
}

export default function App() {
  return (
    <AppProvider>
      <Pages />
    </AppProvider>
  )
}
