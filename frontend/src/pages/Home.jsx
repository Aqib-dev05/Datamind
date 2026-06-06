import { useState, useRef } from 'react'
import { useApp } from '../context/AppContext'
import { uploadFile, fetchQuestions } from '../services/api'
import './Home.css'

export default function Home() {
  const { setFileData, setQuestions, setStep } = useApp()
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [fileName, setFileName] = useState('')
  const inputRef = useRef()

  const handleFile = async (file) => {
    if (!file) return
    const ext = file.name.split('.').pop().toLowerCase()
    if (!['xlsx', 'xls', 'csv'].includes(ext)) {
      setError('Only .xlsx, .xls, or .csv files are allowed.')
      return
    }
    setError('')
    setFileName(file.name)
    setLoading(true)
    try {
      const uploaded = await uploadFile(file)
      setFileData(uploaded)
      const qData = await fetchQuestions(uploaded.file_id)
      setQuestions(qData.questions)
      setStep('questions')
    } catch (e) {
      setError(e.response?.data?.detail || 'Upload failed. Try again.')
    } finally {
      setLoading(false)
    }
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  return (
    <div className="home-wrap">
      {/* Background grid */}
      <div className="grid-bg" />

      <div className="home-inner">
        {/* Header */}
        <header className="home-header animate-fadeUp">
          <div className="logo-chip">
            <span className="logo-icon">⬡</span>
            <span className="logo-text">DataMind AI</span>
          </div>
          <p className="home-tagline">Upload messy data. AI cleans it.</p>
        </header>

        {/* Upload Card */}
        <div className="upload-card animate-fadeUp delay-1">
          <div
            className={`drop-zone ${dragging ? 'dragging' : ''} ${loading ? 'loading-state' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => !loading && inputRef.current.click()}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".xlsx,.xls,.csv"
              hidden
              onChange={(e) => handleFile(e.target.files[0])}
            />

            {loading ? (
              <div className="upload-loading">
                <div className="spinner" />
                <p className="upload-loading-text">Analyzing <span className="font-mono">{fileName}</span>...</p>
                <p className="upload-sub">AI is reading your file</p>
              </div>
            ) : (
              <div className="upload-idle">
                <div className="upload-icon-wrap">
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                    <polyline points="17 8 12 3 7 8"/>
                    <line x1="12" y1="3" x2="12" y2="15"/>
                  </svg>
                </div>
                <p className="upload-main">Drop your file here</p>
                <p className="upload-sub">or click to browse</p>
                <div className="upload-formats">
                  <span className="fmt-tag">.xlsx</span>
                  <span className="fmt-tag">.xls</span>
                  <span className="fmt-tag">.csv</span>
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="error-banner animate-fadeIn">
              <span>⚠</span> {error}
            </div>
          )}
        </div>

        {/* Features */}
        <div className="features animate-fadeUp delay-2">
          {[
            { icon: '◈', label: 'AI Analyzes', desc: 'Detects issues in your data' },
            { icon: '◉', label: 'Smart Questions', desc: 'Asks before changing anything' },
            { icon: '◆', label: 'Clean Export', desc: 'Download as CSV or Excel' },
          ].map((f) => (
            <div key={f.label} className="feature-item">
              <span className="feature-icon">{f.icon}</span>
              <div>
                <p className="feature-label">{f.label}</p>
                <p className="feature-desc">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
