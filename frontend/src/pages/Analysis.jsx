import { useState } from 'react'
import { useApp } from '../context/AppContext'
import { processFile } from '../services/api'
import './Analysis.css'
 
export default function Analysis() {
  const { fileData, questions, setResult, setStep, reset } = useApp()
  const [answers, setAnswers] = useState({})
  const [outputFormat, setOutputFormat] = useState('xlsx')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
 
  const handleRadio = (qId, value) => {
    setAnswers((prev) => ({ ...prev, [qId]: value }))
  }
 
  const handleCheckbox = (qId, value, checked) => {
    setAnswers((prev) => {
      const current = Array.isArray(prev[qId]) ? prev[qId] : []
      if (checked) return { ...prev, [qId]: [...current, value] }
      return { ...prev, [qId]: current.filter((v) => v !== value) }
    })
  }
 
  const handleProcess = async () => {
    setError('')
    setLoading(true)
    try {
      const res = await processFile(fileData.file_id, answers, outputFormat)
      setResult({ ...res, outputFormat })
      setStep('result')
    } catch (e) {
      setError(e.response?.data?.detail || 'Processing failed. Try again.')
    } finally {
      setLoading(false)
    }
  }
 
  return (
    <div className="analysis-wrap">
      <div className="grid-bg" />
 
      <div className="analysis-inner">
        {/* Top bar */}
        <div className="analysis-topbar animate-fadeUp">
          <button className="back-btn" onClick={reset}>← Back</button>
          <div className="file-chip">
            <span className="file-chip-icon">⬡</span>
            <span className="font-mono">{fileData?.filename}</span>
          </div>
        </div>
 
        {/* File summary */}
        <div className="file-summary animate-fadeUp delay-1">
          <h1 className="analysis-title">AI found some issues</h1>
          <p className="analysis-sub">Answer these questions before we clean your file.</p>
 
          <div className="summary-chips">
            <div className="summary-chip">
              <span className="chip-val">{fileData?.rows?.toLocaleString()}</span>
              <span className="chip-label">Rows</span>
            </div>
            <div className="summary-chip">
              <span className="chip-val">{fileData?.columns}</span>
              <span className="chip-label">Columns</span>
            </div>
            <div className="summary-chip warn">
              <span className="chip-val">{fileData?.duplicate_rows}</span>
              <span className="chip-label">Duplicates</span>
            </div>
            <div className="summary-chip warn">
              <span className="chip-val">{fileData?.total_missing}</span>
              <span className="chip-label">Missing</span>
            </div>
          </div>
        </div>
 
        {/* Questions */}
        <div className="questions-list">
          {questions.map((q, i) => (
            <div key={q.id} className="question-card animate-fadeUp" style={{ animationDelay: `${0.1 * (i + 2)}s` }}>
              <div className="q-header">
                <span className="q-num font-mono">Q{i + 1}</span>
                <p className="q-text">{q.question}</p>
              </div>
 
              <div className="q-options">
                {q.type === 'radio' && q.options?.map((opt) => (
                  <label key={opt.id} className={`option-label ${answers[q.id] === opt.label ? 'selected' : ''}`}>
                    <input
                      type="radio"
                      name={q.id}
                      value={opt.label}
                      checked={answers[q.id] === opt.label}
                      onChange={() => handleRadio(q.id, opt.label)}
                      hidden
                    />
                    <span className="radio-dot" />
                    {opt.label}
                  </label>
                ))}
 
                {q.type === 'checkbox' && q.options?.map((opt) => {
                  const checked = Array.isArray(answers[q.id]) && answers[q.id].includes(opt.label)
                  return (
                    <label key={opt.id} className={`option-label ${checked ? 'selected' : ''}`}>
                      <input
                        type="checkbox"
                        value={opt.label}
                        checked={checked}
                        onChange={(e) => handleCheckbox(q.id, opt.label, e.target.checked)}
                        hidden
                      />
                      <span className="check-box">{checked ? '✓' : ''}</span>
                      {opt.label}
                    </label>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
 
        {/* Output Format */}
        <div className="format-card animate-fadeUp">
          <p className="format-title">Output Format</p>
          <p className="format-sub">How do you want to download the cleaned file?</p>
          <div className="format-options">
            {[
              { value: 'xlsx', label: 'Excel', icon: '📊', desc: '.xlsx file' },
              { value: 'csv', label: 'CSV', icon: '📄', desc: '.csv file' },
            ].map((fmt) => (
              <button
                key={fmt.value}
                className={`format-btn ${outputFormat === fmt.value ? 'active' : ''}`}
                onClick={() => setOutputFormat(fmt.value)}
              >
                <span className="fmt-icon">{fmt.icon}</span>
                <span className="fmt-label">{fmt.label}</span>
                <span className="fmt-desc">{fmt.desc}</span>
              </button>
            ))}
          </div>
        </div>
 
        {error && (
          <div className="error-banner animate-fadeIn">
            <span>⚠</span> {error}
          </div>
        )}
 
        {/* Process Button */}
        <button
          className={`process-btn ${loading ? 'loading' : ''}`}
          onClick={handleProcess}
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="btn-spinner" />
              Processing your file...
            </>
          ) : (
            <>Clean & Download →</>
          )}
        </button>
      </div>
    </div>
  )
}
