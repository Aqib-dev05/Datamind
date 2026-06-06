import { createContext, useContext, useState } from 'react'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [fileData, setFileData] = useState(null)      // upload response
  const [questions, setQuestions] = useState([])       // AI questions
  const [result, setResult] = useState(null)           // process response
  const [step, setStep] = useState('upload')           // upload | questions | result

  const reset = () => {
    setFileData(null)
    setQuestions([])
    setResult(null)
    setStep('upload')
  }

  return (
    <AppContext.Provider value={{ fileData, setFileData, questions, setQuestions, result, setResult, step, setStep, reset }}>
      {children}
    </AppContext.Provider>
  )
}

export const useApp = () => useContext(AppContext)
