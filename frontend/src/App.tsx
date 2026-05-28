import React, { useState, useEffect, useRef } from 'react'

interface Manager {
  ps_no: number | null;
  name: string | null;
  email_id: string | null;
}

interface InternalExp {
  Org: string;
  From: string;
  To: string;
}

interface ExternalExp {
  Org: string;
  Designation?: string;
  From: string;
  To: string;
}

interface Segment {
  Segment: string;
  "Sub-Segment": string;
}

interface Skill {
  Skill: string;
  "Sub-Skill": string;
  User_Declared_Proficiency?: string;
  Reviewed_Proficiency?: string;
  Is_Core_Skill?: string;
}

interface Qualification {
  Year: number | null;
  Description: string;
}

interface EmployeeProfile {
  ps_no: number;
  staff_name: string;
  email_id: string;
  mobile: string;
  cadre: string;
  band: string;
  designation: string;
  total_exp: number;
  internal_exp_years: number;
  external_exp_years: number;
  job_code: string;
  job_name: string;
  cluster: string;
  bu: string;
  sbg: string;
  manager: Manager;
  internal_experience: InternalExp[];
  external_experience: ExternalExp[];
  segment_exposure: Segment[];
  skills: Skill[];
  certifications: string[];
  qualifications: Qualification[];
  similarity_score?: number;
}

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  results?: EmployeeProfile[];
  active_filters?: Record<string, any>;
  timestamp: Date;
}

export default function App() {
  const [sessionId, setSessionId] = useState<string>('')
  const [messages, setMessages] = useState<Message[]>([])
  const [inputText, setInputText] = useState<string>('')
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [dbStatus, setDbStatus] = useState<{ loaded: boolean; count: number; filename: string }>({
    loaded: false,
    count: 0,
    filename: ''
  })
  const [activeFilters, setActiveFilters] = useState<Record<string, any>>({})
  const [expandedEmployee, setExpandedEmployee] = useState<number | null>(null)
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('theme') as 'light' | 'dark') || 'light'
  })
  
  const fileInputRef = useRef<HTMLInputElement>(null)
  const feedEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  // 1. Initialize session and check health
  useEffect(() => {
    // Session persistence in localStorage
    let sid = localStorage.getItem('workforce_session_id')
    if (!sid) {
      sid = 'session_' + Math.random().toString(36).substring(2, 11)
      localStorage.setItem('workforce_session_id', sid)
    }
    setSessionId(sid)
    checkBackendHealth()
  }, [])

  // 2. Scroll to bottom on new messages
  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const checkBackendHealth = async () => {
    try {
      const res = await fetch('/api/health')
      if (res.ok) {
        const data = await res.json()
        setDbStatus({
          loaded: data.database_loaded,
          count: data.profiles_count,
          filename: data.source_file || 'synthetic_skill_dataset.xlsx'
        })
      }
    } catch (e) {
      console.error('Failed to connect to backend', e)
    }
  }

  // 3. Handle File Upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    setIsLoading(true)
    try {
      const res = await fetch('/api/upload-workbook', {
        method: 'POST',
        body: formData
      })

      if (res.ok) {
        const data = await res.json()
        setDbStatus({
          loaded: true,
          count: data.profiles_count,
          filename: data.filename
        })
        
        // Clear existing history and active filters for the new dataset
        setMessages([
          {
            id: 'upload_msg_' + Date.now(),
            sender: 'assistant',
            text: `Successfully uploaded ${data.filename}. Loaded ${data.profiles_count} profiles. Ask me anything!`,
            timestamp: new Date()
          }
        ])
        setActiveFilters({})
        setExpandedEmployee(null)
      } else {
        const errData = await res.json()
        alert('Upload failed: ' + (errData.detail || 'Invalid schema'))
      }
    } catch (err) {
      alert('Error uploading file: ' + err)
    } finally {
      setIsLoading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  // 4. Handle sending a chat message
  const handleSendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!inputText.trim() || isLoading) return

    const userText = inputText
    setInputText('')
    
    // Add User Message to feed
    const userMsgId = 'user_msg_' + Date.now()
    setMessages(prev => [
      ...prev,
      {
        id: userMsgId,
        sender: 'user',
        text: userText,
        timestamp: new Date()
      }
    ])

    setIsLoading(true)
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: userText,
          top_k: 10
        })
      })

      if (res.ok) {
        const data = await res.json()
        setActiveFilters(data.active_filters || {})
        
        setMessages(prev => [
          ...prev,
          {
            id: 'assistant_msg_' + Date.now(),
            sender: 'assistant',
            text: data.message,
            results: data.results,
            active_filters: data.active_filters,
            timestamp: new Date()
          }
        ])
      } else {
        const errData = await res.json()
        setMessages(prev => [
          ...prev,
          {
            id: 'assistant_err_' + Date.now(),
            sender: 'assistant',
            text: `Error: ${errData.detail || 'Could not parse query'}`,
            timestamp: new Date()
          }
        ])
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          id: 'assistant_err_' + Date.now(),
          sender: 'assistant',
          text: 'Error communicating with backend service.',
          timestamp: new Date()
        }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  // 5. Reset conversation session
  const handleResetSession = async () => {
    if (!window.confirm('Are you sure you want to reset filters and conversation?')) return
    
    try {
      const res = await fetch('/api/reset-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ session_id: sessionId })
      })

      if (res.ok) {
        setMessages([])
        setActiveFilters({})
        setExpandedEmployee(null)
        setMessages([
          {
            id: 'reset_notice',
            sender: 'assistant',
            text: 'Filters and session history have been reset. Ask me a new query!',
            timestamp: new Date()
          }
        ])
      }
    } catch (e) {
      alert('Failed to reset session')
    }
  }

  const toggleEmployeeExpand = (psNo: number) => {
    setExpandedEmployee(prev => (prev === psNo ? null : psNo))
  }

  const isSkillHighlighted = (sk: Skill) => {
    if (sk.Is_Core_Skill === 'Yes') return true
    
    const skillName = (sk.Skill || '').toLowerCase()
    const subSkillName = (sk['Sub-Skill'] || '').toLowerCase()
    
    if (activeFilters.skill && (
      skillName.includes(activeFilters.skill.toLowerCase()) || 
      subSkillName.includes(activeFilters.skill.toLowerCase()) ||
      activeFilters.skill.toLowerCase().includes(skillName) ||
      activeFilters.skill.toLowerCase().includes(subSkillName)
    )) {
      return true
    }
    
    if (activeFilters.sub_skill && (
      skillName.includes(activeFilters.sub_skill.toLowerCase()) || 
      subSkillName.includes(activeFilters.sub_skill.toLowerCase()) ||
      activeFilters.sub_skill.toLowerCase().includes(skillName) ||
      activeFilters.sub_skill.toLowerCase().includes(subSkillName)
    )) {
      return true
    }

    if (activeFilters.skills_text && (
      skillName.includes(activeFilters.skills_text.toLowerCase()) ||
      subSkillName.includes(activeFilters.skills_text.toLowerCase()) ||
      activeFilters.skills_text.toLowerCase().includes(skillName) ||
      activeFilters.skills_text.toLowerCase().includes(subSkillName)
    )) {
      return true
    }

    // Check last user query text
    const lastUserMsg = [...messages].reverse().find(m => m.sender === 'user')
    if (lastUserMsg) {
      const text = lastUserMsg.text.toLowerCase()
      if (text.includes(skillName) || text.includes(subSkillName)) {
        return true
      }
    }

    return false
  }

  const isMainSkillHighlighted = (mainSkillName: string, skills: Skill[]) => {
    return skills.filter(sk => sk.Skill === mainSkillName).some(sk => isSkillHighlighted(sk))
  }


  return (
    <div className="app-container">
      {/* Sidebar Panel */}
      <aside className="sidebar">
        <div className="logo-container">
          <img src="https://upload.wikimedia.org/wikipedia/commons/4/4a/L%26T.svg" alt="L&T Logo" className="logo-img" />
          <div className="logo-text">Workforce AI</div>
          <button 
            type="button"
            className="theme-toggle-btn"
            onClick={() => setTheme(prev => prev === 'light' ? 'dark' : 'light')}
            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            style={{ fontSize: '0.75rem', padding: '4px 8px' }}
          >
            {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
          </button>
        </div>

        {/* Database Upload Box */}
        <div className="section-title">Knowledge Source</div>
        <div className="upload-zone" onClick={() => fileInputRef.current?.click()}>
          <div className="upload-icon">📁</div>
          <div className="upload-text">
            {dbStatus.loaded ? 'Update Workbook' : 'Upload Relational Workbook'}
          </div>
          <div className="upload-subtext">
            {dbStatus.loaded ? dbStatus.filename : 'Drag or click to choose (.xlsx)'}
          </div>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            style={{ display: 'none' }}
            accept=".xlsx, .xls"
          />
        </div>

        {/* Active Filters Block */}
        <div className="section-title">Active Filters</div>
        {Object.keys(activeFilters).length > 0 ? (
          <div className="filter-tag-container">
            {Object.entries(activeFilters).map(([key, val]) => (
              <span key={key} className="filter-tag">
                {key.replace('_', ' ')}: {String(val)}
              </span>
            ))}
          </div>
        ) : (
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
            No active filters. Ask questions like "show civil engineers" to apply filters.
          </div>
        )}

        {/* Reset Session Action */}
        <button className="btn btn-secondary" onClick={handleResetSession}>
          Reset Session
        </button>
      </aside>

      {/* Chat Window Panel */}
      <main className="main-chat">
        {/* Chat Header */}
        <header className="chat-header">
          <div className="header-title">
            <h1>Workforce Intelligence Chatbot</h1>
          </div>
          <div className="header-status">
            <span className={`status-dot ${dbStatus.loaded ? 'active' : ''}`} />
            <span>
              {dbStatus.loaded 
                ? `Ready: ${dbStatus.count} employees indexed (${dbStatus.filename})`
                : 'Awaiting workbook loading...'
              }
            </span>
          </div>
        </header>

        {/* Chat Message Feed */}
        <section className="message-feed">
          {messages.length === 0 && (
            <div className="msg-row assistant">
              <div className="msg-bubble">
                <p>Hello! I am your Enterprise Workforce Intelligence Assistant.</p>
                <p style={{ marginTop: '0.5rem' }}>
                  You can search and filter the employee database using natural language. For example:
                </p>
                <ul style={{ margin: '0.75rem 0 0 1.25rem' }}>
                  <li>"show civil engineers in Chennai with 10+ years experience"</li>
                  <li>"find PMP certified project managers with Siemens experience"</li>
                  <li>"who knows electrical systems and has reviewed proficiency"</li>
                </ul>
              </div>
            </div>
          )}

          {messages.map(msg => (
            <div key={msg.id} className={`msg-row ${msg.sender}`}>
              <div className="msg-bubble">
                <div>{msg.text}</div>

                {/* Search Result Profile Cards */}
                {msg.results && msg.results.length > 0 && (
                  <div className="employee-grid">
                    {msg.results.map(emp => {
                      const isExpanded = expandedEmployee === emp.ps_no
                      return (
                        <div 
                          key={emp.ps_no} 
                          className="profile-card"
                          onClick={() => toggleEmployeeExpand(emp.ps_no)}
                        >
                          {emp.similarity_score !== undefined && emp.similarity_score > 0 && (
                            <span className="match-badge">
                              {Math.round(emp.similarity_score * 100)}% Match
                            </span>
                          )}
                          <div className="profile-name">{emp.staff_name}</div>
                          <div className="profile-title">{emp.designation} (PS No: {emp.ps_no})</div>
                          
                          <div className="profile-detail-row" style={{ marginTop: '0.5rem' }}>
                            <span>Total Exp:</span>
                            <span>{emp.total_exp} yrs</span>
                          </div>
                          <div className="profile-detail-row">
                            <span>Cluster/BU:</span>
                            <span>{emp.cluster} / {emp.bu}</span>
                          </div>
                          <div className="profile-detail-row">
                            <span>Cadre / Band:</span>
                            <span>{emp.cadre} / {emp.band}</span>
                          </div>

                          {/* Skills display */}
                          {!isExpanded ? (
                            <>
                              <div className="section-title" style={{ marginTop: '0.5rem', marginBottom: '0.25rem', fontSize: '0.65rem' }}>Skills</div>
                              <div className="skills-container">
                                {Array.from(new Set(emp.skills.map(sk => sk.Skill).filter(Boolean))).slice(0, 4).map((mainSkill, idx) => (
                                  <span key={idx} className={`skill-pill ${isMainSkillHighlighted(mainSkill, emp.skills) ? 'core' : ''}`}>
                                    {mainSkill}
                                  </span>
                                ))}
                                {Array.from(new Set(emp.skills.map(sk => sk.Skill).filter(Boolean))).length > 4 && (
                                  <span className="skill-pill">+{Array.from(new Set(emp.skills.map(sk => sk.Skill).filter(Boolean))).length - 4} more</span>
                                )}
                              </div>
                            </>
                          ) : (
                            <>
                              <div className="section-title" style={{ marginTop: '0.5rem', marginBottom: '0.25rem', fontSize: '0.65rem' }}>Skills</div>
                              <div className="skills-container">
                                {Array.from(new Set(emp.skills.map(sk => sk.Skill).filter(Boolean))).map((mainSkill, idx) => (
                                  <span key={idx} className={`skill-pill ${isMainSkillHighlighted(mainSkill, emp.skills) ? 'core' : ''}`}>
                                    {mainSkill}
                                  </span>
                                ))}
                              </div>
                              <div className="section-title" style={{ marginTop: '0.75rem', marginBottom: '0.25rem', fontSize: '0.65rem' }}>Sub-Skills</div>
                              <div className="skills-container">
                                {emp.skills.map((sk, idx) => (
                                  <span key={idx} className={`skill-pill ${isSkillHighlighted(sk) ? 'core' : ''}`}>
                                    {sk['Sub-Skill']} {sk.Reviewed_Proficiency ? `(${sk.Reviewed_Proficiency})` : ''}
                                  </span>
                                ))}
                              </div>
                            </>
                          )}

                          {/* Expanded Timeline Details */}
                          {isExpanded && (
                            <div style={{ marginTop: '0.75rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem', animation: 'fadeIn 0.2s ease' }} onClick={e => e.stopPropagation()}>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                                <strong>Contact:</strong> {emp.email_id} | {emp.mobile}
                              </div>
                              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                                <strong>Qualifications:</strong> {emp.qualifications.map(q => `${q.Description} (${q.Year})`).join(', ')}
                              </div>
                              {emp.certifications.length > 0 && (
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                                  <strong>Certifications:</strong> {emp.certifications.join(', ')}
                                </div>
                              )}
                              {emp.internal_experience.length > 0 && (
                                <div style={{ marginTop: '0.5rem' }}>
                                  <strong style={{ fontSize: '0.75rem' }}>Internal Projects:</strong>
                                  <ul style={{ fontSize: '0.7rem', paddingLeft: '1rem', marginTop: '0.25rem', color: 'var(--text-muted)' }}>
                                    {emp.internal_experience.map((exp, idx) => (
                                      <li key={idx}>{exp.Org} ({exp.From} to {exp.To})</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {emp.external_experience.length > 0 && (
                                <div style={{ marginTop: '0.5rem' }}>
                                  <strong style={{ fontSize: '0.75rem' }}>External Work History:</strong>
                                  <ul style={{ fontSize: '0.7rem', paddingLeft: '1rem', marginTop: '0.25rem', color: 'var(--text-muted)' }}>
                                    {emp.external_experience.map((exp, idx) => (
                                      <li key={idx}>{exp.Org} as {exp.Designation || 'Engineer'} ({exp.From} to {exp.To})</li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Loading / Typing Indicator */}
          {isLoading && (
            <div className="msg-row assistant">
              <div className="msg-bubble">
                <div className="typing-indicator">
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                </div>
              </div>
            </div>
          )}
          <div ref={feedEndRef} />
        </section>

        {/* Input Bar */}
        <form onSubmit={handleSendMessage} className="chat-input-bar">
          <div className="input-container">
            <input
              type="text"
              className="chat-input"
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              placeholder={dbStatus.loaded ? "Ask a query, e.g. 'find civil engineers with metro exposure'..." : "Please upload a relational workbook to get started."}
              disabled={isLoading || !dbStatus.loaded}
            />
            <button 
              type="submit" 
              className="send-btn" 
              disabled={isLoading || !inputText.trim() || !dbStatus.loaded}
            >
              ➔
            </button>
          </div>
        </form>
      </main>
    </div>
  )
}
