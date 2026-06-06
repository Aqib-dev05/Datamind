import { useApp } from '../context/AppContext'
import { getDownloadUrl } from '../services/api'
import './Results.css'

export default function Results() {
  const { result, fileData, reset } = useApp()
  const { stats, summary, outputFormat, download_url } = result || {}

  const downloadUrl = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}${download_url}`

  const statItems = [
    { label: 'Original Rows', value: stats?.original_rows?.toLocaleString(), icon: '◈' },
    { label: 'Final Rows',    value: stats?.final_rows?.toLocaleString(),    icon: '◆', accent: true },
    { label: 'Rows Removed',  value: stats?.rows_removed?.toLocaleString(), icon: '◉', warn: stats?.rows_removed > 0 },
    { label: 'Duplicates Removed', value: stats?.duplicates_removed?.toLocaleString(), icon: '⊗' },
  ]

  return (
    <div className="results-wrap">
      <div className="grid-bg" />

      <div className="results-inner">
        {/* Header */}
        <div className="results-header animate-fadeUp">
          <div className="success-badge">
            <span className="success-icon">✓</span>
            <span>File Cleaned Successfully</span>
          </div>
          <h1 className="results-title">Your data is ready</h1>
          <p className="results-sub">{summary}</p>
        </div>

        {/* Stats Grid */}
        <div className="stats-grid animate-fadeUp delay-1">
          {statItems.map((s) => (
            <div key={s.label} className={`stat-card ${s.accent ? 'accent' : ''} ${s.warn ? 'warn' : ''}`}>
              <span className="stat-icon">{s.icon}</span>
              <span className="stat-val">{s.value}</span>
              <span className="stat-label">{s.label}</span>
            </div>
          ))}
        </div>

        {/* Missing Handled */}
        {stats?.missing_handled && Object.keys(stats.missing_handled).length > 0 && (
          <div className="detail-card animate-fadeUp delay-2">
            <p className="detail-title">Missing Values Handled</p>
            <div className="detail-list">
              {Object.entries(stats.missing_handled).map(([col, action]) => (
                <div key={col} className="detail-row">
                  <span className="font-mono detail-col">{col}</span>
                  <span className="detail-action">{action}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Columns Cleaned */}
        {stats?.columns_cleaned?.length > 0 && (
          <div className="detail-card animate-fadeUp delay-3">
            <p className="detail-title">Columns Cleaned</p>
            <div className="cols-list">
              {stats.columns_cleaned.map((col) => (
                <span key={col} className="col-tag font-mono">{col}</span>
              ))}
            </div>
          </div>
        )}

        {/* Download */}
        <div className="download-card animate-fadeUp delay-3">
          <div className="download-info">
            <span className="download-icon">{outputFormat === 'csv' ? '📄' : '📊'}</span>
            <div>
              <p className="download-label">cleaned_data.{outputFormat}</p>
              <p className="download-sub">Ready to download · {outputFormat.toUpperCase()}</p>
            </div>
          </div>
          <a href={downloadUrl} download className="download-btn">
            Download ↓
          </a>
        </div>

        {/* Actions */}
        <button className="restart-btn animate-fadeUp delay-4" onClick={reset}>
          ← Analyze Another File
        </button>
      </div>
    </div>
  )
}
