import { useState, useEffect, useCallback, useRef } from 'react'

const STORAGE_KEY = 'agent-control-room'
const DEFAULT_BACKEND_URL = 'http://127.0.0.1:8000'

const taskDescriptions = {
  chat: 'General chat and coding help',
  fix_file: 'Patch a file using the backend agent',
  generate_tests: 'Produce tests from current context',
  validate_workspace: 'Run a broader workspace validation pass',
}

function App() {
  const [backendUrl, setBackendUrl] = useState(DEFAULT_BACKEND_URL)
  const [task, setTask] = useState('chat')
  const [message, setMessage] = useState('')
  const [filePath, setFilePath] = useState('')
  const [relativeFilePath, setRelativeFilePath] = useState('')
  const [code, setCode] = useState('')
  const [language, setLanguage] = useState('python')
  const [autonomousMode, setAutonomousMode] = useState(true)
  const [runValidation, setRunValidation] = useState(false)
  const [generateTests, setGenerateTests] = useState(false)
  const [intelligenceLevel, setIntelligenceLevel] = useState('high')
  const [status, setStatus] = useState('Idle')
  const [response, setResponse] = useState('No response yet.')
  const [updatedFiles, setUpdatedFiles] = useState([])
  const [loading, setLoading] = useState(false)
  const [expandedFileIndex, setExpandedFileIndex] = useState(null)
  const responseRef = useRef(null)

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const data = JSON.parse(saved)
        setBackendUrl(data.backendUrl || DEFAULT_BACKEND_URL)
        setTask(data.task || 'chat')
        setFilePath(data.filePath || '')
        setRelativeFilePath(data.relativeFilePath || '')
        setLanguage(data.language || 'python')
        setAutonomousMode(data.autonomousMode !== false)
        setRunValidation(data.runValidation || false)
        setGenerateTests(data.generateTests || false)
        setIntelligenceLevel(data.intelligenceLevel || 'high')
      } catch {
        // Ignore invalid persisted UI state.
      }
    }
  }, [])

  const saveSettings = useCallback(() => {
    const data = {
      backendUrl,
      task,
      filePath,
      relativeFilePath,
      language,
      autonomousMode,
      runValidation,
      generateTests,
      intelligenceLevel,
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  }, [
    backendUrl,
    task,
    filePath,
    relativeFilePath,
    language,
    autonomousMode,
    runValidation,
    generateTests,
    intelligenceLevel,
  ])

  const buildPayload = useCallback(
    () => ({
      task,
      message: message.trim(),
      filePath: filePath.trim() || undefined,
      relativeFilePath: relativeFilePath.trim() || undefined,
      language: language.trim() || undefined,
      code: code.trim() || undefined,
      runValidation,
      generateTests,
      autonomousMode,
      intelligenceLevel,
    }),
    [
      task,
      message,
      filePath,
      relativeFilePath,
      language,
      code,
      runValidation,
      generateTests,
      autonomousMode,
      intelligenceLevel,
    ],
  )

  const callAgent = useCallback(async () => {
    const payload = buildPayload()
    if (!payload.message) {
      setStatus('Enter a prompt first.')
      return
    }

    saveSettings()
    setLoading(true)
    setStatus('Agent is thinking and executing...')
    setExpandedFileIndex(null)

    try {
      const url = `${backendUrl.replace(/\/$/, '')}/chat`
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const text = await res.text()
        throw new Error(`HTTP ${res.status}: ${text}`)
      }

      const result = await res.json()
      setResponse(result.response || '(empty response)')
      setUpdatedFiles(Array.isArray(result.updatedFiles) ? result.updatedFiles : [])
      setStatus('Completed successfully.')
    } catch (error) {
      const text = error instanceof Error ? error.message : String(error)
      setResponse(text)
      setStatus('Request failed.')
    } finally {
      setLoading(false)
    }
  }, [backendUrl, buildPayload, saveSettings])

  const clearOutput = useCallback(() => {
    setResponse('No response yet.')
    setUpdatedFiles([])
    setExpandedFileIndex(null)
    setStatus('Idle')
  }, [])

  useEffect(() => {
    responseRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [response, updatedFiles])

  const statusClass =
    status === 'Completed successfully.' ? 'ok' : status.includes('failed') ? 'err' : ''

  const statItems = [
    { label: 'Task', value: task.replace('_', ' ') },
    { label: 'Modeling', value: intelligenceLevel.replace('_', ' ') },
    { label: 'Files', value: String(updatedFiles.length) },
  ]

  return (
    <div className="app-shell">
      <div className="lava lava-one" />
      <div className="lava lava-two" />
      <div className="lava lava-three" />

      <aside className="sidebar panel">
        <div className="brand-block">
          <div className="brand-mark">AI</div>
          <div>
            <p className="eyebrow">Lava Workspace</p>
            <h1>Agent Console</h1>
            <p className="muted">
              ChatGPT-inspired control surface with ember orange over carbon black.
            </p>
          </div>
        </div>

        <div className="sidebar-section">
          <p className="section-label">Session</p>
          <div className="stat-grid">
            {statItems.map((item) => (
              <article key={item.label} className="stat-card">
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </article>
            ))}
          </div>
        </div>

        <div className="sidebar-section">
          <p className="section-label">Mode</p>
          <div className="task-pills">
            {Object.entries(taskDescriptions).map(([value, description]) => (
              <button
                key={value}
                type="button"
                className={`task-pill ${task === value ? 'active' : ''}`}
                onClick={() => setTask(value)}
              >
                <strong>{value.replace('_', ' ')}</strong>
                <span>{description}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="sidebar-section compact-stack">
          <label>
            Backend URL
            <input value={backendUrl} onChange={(e) => setBackendUrl(e.target.value)} type="text" />
          </label>
          <label>
            Intelligence
            <select value={intelligenceLevel} onChange={(e) => setIntelligenceLevel(e.target.value)}>
              <option value="high">high</option>
              <option value="very_high">very high</option>
              <option value="medium">medium</option>
            </select>
          </label>
          <label>
            Language
            <input value={language} onChange={(e) => setLanguage(e.target.value)} placeholder="python" />
          </label>
        </div>

        <div className="toggle-list">
          <label className="toggle">
            <input
              type="checkbox"
              checked={autonomousMode}
              onChange={(e) => setAutonomousMode(e.target.checked)}
            />
            <span>Autonomous mode</span>
          </label>
          <label className="toggle">
            <input
              type="checkbox"
              checked={runValidation}
              onChange={(e) => setRunValidation(e.target.checked)}
            />
            <span>Run validation</span>
          </label>
          <label className="toggle">
            <input
              type="checkbox"
              checked={generateTests}
              onChange={(e) => setGenerateTests(e.target.checked)}
            />
            <span>Generate tests</span>
          </label>
        </div>
      </aside>

      <main className="chat-stage">
        <section className="panel topbar">
          <div>
            <p className="eyebrow">Operator View</p>
            <h2>{task.replace('_', ' ')} workflow</h2>
          </div>
          <div className={`status-pill ${statusClass}`}>{loading ? 'Running' : status}</div>
        </section>

        <section className="panel conversation">
          <div className="messages">
            <article className="message assistant intro">
              <div className="avatar ember">AI</div>
              <div className="bubble">
                <p className="message-role">Assistant</p>
                <h3>Orange ember chat workspace</h3>
                <p>
                  Configure the agent on the left, send your prompt below, and inspect returned files in
                  an integrated response stream.
                </p>
              </div>
            </article>

            <article className="message user">
              <div className="bubble user-bubble">
                <p className="message-role">Prompt</p>
                <p>{message.trim() || 'Your prompt will appear here once you start typing.'}</p>
              </div>
            </article>

            <article className="message assistant">
              <div className="avatar glow">AG</div>
              <div className="bubble response-bubble">
                <p className="message-role">Agent Response</p>
                <pre ref={responseRef}>{response}</pre>
              </div>
            </article>
          </div>
        </section>

        <section className="panel composer-panel">
          <div className="composer-head">
            <div>
              <p className="section-label">Composer</p>
              <h3>Describe the change or question</h3>
            </div>
            <div className="composer-actions">
              <button onClick={clearOutput} className="btn ghost" type="button">
                Clear
              </button>
              <button onClick={callAgent} disabled={loading} className="btn primary" type="button">
                {loading ? 'Running...' : 'Send to Agent'}
              </button>
            </div>
          </div>

          <label className="prompt-box">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={5}
              placeholder="Tell the agent what to build, refactor, explain, or fix..."
            />
          </label>

          <div className="meta-grid">
            <label>
              File Path
              <input value={filePath} onChange={(e) => setFilePath(e.target.value)} placeholder="app.py" />
            </label>
            <label>
              Relative Path
              <input
                value={relativeFilePath}
                onChange={(e) => setRelativeFilePath(e.target.value)}
                placeholder="src/app.py"
              />
            </label>
          </div>

          <label>
            Code Context
            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              rows={7}
              placeholder="Paste surrounding code when you want the backend to work with richer context..."
            />
          </label>
        </section>

        <section className="panel files-panel">
          <div className="files-header">
            <div>
              <p className="section-label">Artifacts</p>
              <h3>Updated files</h3>
            </div>
            <span className="file-count">{updatedFiles.length} returned</span>
          </div>

          <div className="files-list">
            {updatedFiles.length === 0 ? (
              <p className="empty-state">No changed files returned by the backend yet.</p>
            ) : (
              updatedFiles.map((item, index) => {
                const isOpen = expandedFileIndex === index
                return (
                  <article key={index} className={`file-card ${isOpen ? 'open' : ''}`}>
                    <button
                      type="button"
                      className="file-head"
                      onClick={() => setExpandedFileIndex(isOpen ? null : index)}
                    >
                      <span>{item.path || `updated-file-${index + 1}`}</span>
                      <span>{isOpen ? 'Hide' : 'View'}</span>
                    </button>
                    {isOpen ? (
                      <div className="file-content">
                        <pre>{typeof item.content === 'string' ? item.content : ''}</pre>
                      </div>
                    ) : null}
                  </article>
                )
              })
            )}
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
