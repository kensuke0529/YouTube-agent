import { useEffect, useMemo, useState } from 'react'
import ReactMarkdown from 'react-markdown'

const API_BASE = import.meta.env.VITE_API_BASE || (typeof window !== 'undefined' && window.location?.origin?.includes('localhost') ? 'http://localhost:8000' : 'https://youtube-extracter-production.up.railway.app')
const API_KEY = import.meta.env.VITE_API_KEY

async function post<T>(path: string, body: unknown): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  
  // Add API key if available
  if (API_KEY) {
    headers['X-API-Key'] = API_KEY
  }
  
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body)
  })
  
  if (!res.ok) {
    const errorText = await res.text()
    throw new Error(errorText)
  }
  
  return res.json()
}

export default function App() {
  const [url, setUrl] = useState('')
  const [level, setLevel] = useState<'quick' | 'detailed'>('quick')
  const [transcript, setTranscript] = useState('')
  const [summary, setSummary] = useState('')
  const [videoInfo, setVideoInfo] = useState<any>(null)
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState<{ text: string; score: number; metadata: any }[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [apiHealthy, setApiHealthy] = useState<boolean | null>(null)
  const [usageStats, setUsageStats] = useState<any>(null)
  const [progress, setProgress] = useState<string | null>(null)

  // Debug info
  console.log('App loaded, API_BASE:', API_BASE, 'API_KEY:', API_KEY ? 'Set' : 'Not set')
  console.log('Environment:', import.meta.env.MODE)
  console.log('All env vars:', import.meta.env)

  const videoId = useMemo(() => {
    const id = extractYouTubeId(url)
    return id || 'video'
  }, [url])

  // Fetch usage stats
  useEffect(() => {
    async function fetchUsageStats() {
      try {
        const headers: Record<string, string> = {}
        if (API_KEY) {
          headers['X-API-Key'] = API_KEY
        }
        
        const res = await fetch(`${API_BASE}/usage`, { headers })
        if (res.ok) {
          const stats = await res.json()
          setUsageStats(stats)
        }
      } catch (e) {
        // Ignore errors for usage stats
      }
    }
    
    fetchUsageStats()
    const interval = setInterval(fetchUsageStats, 30000) // Update every 30 seconds
    return () => clearInterval(interval)
  }, [])



  async function handleExtractAndSummarize() {
    setError(null)
    setSuccess(null)
    setProgress(null)
    setBusy(true)
    try {
      setProgress('🔄 Extracting subtitles from YouTube...')
      const data = await post<{ text: string; video_info: any; summary: string }>('/subtitles/extract-and-summarize', { 
        url, 
        level 
      })
      
      setTranscript(data.text)
      setVideoInfo(data.video_info)
      setSummary(data.summary)
      setSuccess('✅ Successfully extracted subtitles and generated summary!')
      setProgress(null)
    } catch (e: any) {
      setError(e?.message || 'Failed to extract and summarize')
      setProgress(null)
    } finally {
      setBusy(false)
    }
  }

  async function handleIngest() {
    setError(null)
    setSuccess(null)
    setProgress(null)
    setBusy(true)
    try {
      setProgress('🔄 Processing transcript into chunks...')
      const chunks = chunkText(transcript, 1200)
      
      setProgress('🔄 Generating embeddings and storing in knowledge base...')
      const result = await post<{ count: number; duplicates_skipped: number }>('/rag/ingest', { 
        chunks, 
        video_id: videoId,
        video_info: videoInfo || {}
      })
      
      let message = `✅ Successfully ingested ${result.count} chunks into the knowledge base!`
      if (result.duplicates_skipped > 0) {
        message += ` (${result.duplicates_skipped} duplicates skipped to save costs)`
      }
      setSuccess(message)
      setProgress(null)
    } catch (e: any) {
      setError(e?.message || 'Failed to ingest')
      setProgress(null)
    } finally {
      setBusy(false)
    }
  }

  async function handleAsk() {
    setError(null)
    setSuccess(null)
    setProgress(null)
    setBusy(true)
    try {
      setProgress('🔄 Searching knowledge base and generating answer...')
      const data = await post<{ answer: string; sources: { text: string; score: number; metadata: any }[] }>('/rag/ask', { question })
      setAnswer(data.answer)
      setSources(data.sources)
      setSuccess(`✅ Found answer using ${data.sources.length} sources from the knowledge base!`)
      setProgress(null)
    } catch (e: any) {
      setError(e?.message || 'Failed to get answer')
      setProgress(null)
    } finally {
      setBusy(false)
    }
  }


  return (
    <div className="container">
      <header>
        <h1>YouTube Learning AI</h1>
        <p>Summarize, ingest, and ask questions about any video transcript.</p>
      </header>

      <ApiHealth onResult={setApiHealthy} />
      {apiHealthy === false && (
        <section className="card" style={{ borderColor: 'crimson' }}>
          <strong>API not reachable at:</strong> {API_BASE}
          <div style={{ marginTop: 8 }}>
            Set <code>VITE_API_BASE</code> to your FastAPI URL and redeploy the frontend.
          </div>
        </section>
      )}

      {usageStats && (
        <section className="card" style={{ borderColor: 'blue' }}>
          <h3>📊 Usage Statistics</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginTop: '12px' }}>
            <div>
              <strong>Daily Usage:</strong> {usageStats.total_tokens?.toLocaleString() || 0} / {usageStats.daily_limit?.toLocaleString() || '∞'} tokens
              <div style={{ 
                width: '100%', 
                height: '8px', 
                backgroundColor: 'color-mix(in oklab, CanvasText 10%, Canvas 90%)', 
                borderRadius: '4px', 
                marginTop: '4px',
                overflow: 'hidden'
              }}>
                <div style={{ 
                  width: `${Math.min(100, (usageStats.total_tokens / usageStats.daily_limit) * 100)}%`, 
                  height: '100%', 
                  backgroundColor: usageStats.total_tokens / usageStats.daily_limit > 0.8 ? 'orange' : 'green',
                  transition: 'width 0.3s ease'
                }} />
              </div>
            </div>
            <div>
              <strong>Hourly Usage:</strong> {usageStats.hourly_usage?.toLocaleString() || 0} / {usageStats.hourly_limit?.toLocaleString() || '∞'} tokens
            </div>
            <div>
              <strong>Remaining Today:</strong> {usageStats.daily_remaining?.toLocaleString() || '∞'} tokens
            </div>
            <div>
              <strong>Last Reset:</strong> {usageStats.last_reset ? new Date(usageStats.last_reset).toLocaleString() : 'Unknown'}
            </div>
          </div>
        </section>
      )}


      {error && (
        <section className="card" style={{ borderColor: 'orange', backgroundColor: 'color-mix(in oklab, red 5%, Canvas 95%)' }}>
          <strong>❌ Error:</strong> {error}
        </section>
      )}

      {success && (
        <section className="card" style={{ borderColor: 'green', backgroundColor: 'color-mix(in oklab, green 5%, Canvas 95%)' }}>
          <strong>✅ Success:</strong> {success}
        </section>
      )}

      {progress && (
        <section className="card" style={{ borderColor: 'blue', backgroundColor: 'color-mix(in oklab, blue 5%, Canvas 95%)' }}>
          <strong>🔄 Processing:</strong> {progress}
          <div style={{ 
            width: '100%', 
            height: '4px', 
            backgroundColor: 'color-mix(in oklab, blue 20%, Canvas 80%)', 
            borderRadius: '2px', 
            marginTop: '8px',
            overflow: 'hidden'
          }}>
            <div style={{ 
              width: '100%', 
              height: '100%', 
              backgroundColor: 'blue',
              animation: 'pulse 1.5s ease-in-out infinite'
            }} />
          </div>
        </section>
      )}

      <section className="card">
        <h2>1) Input YouTube URL & Summarize</h2>
        <div className="row">
          <input placeholder="https://www.youtube.com/watch?v=..." value={url} onChange={e => setUrl(e.target.value)} />
          <select value={level} onChange={e => setLevel(e.target.value as any)}>
            <option value="quick">Quick</option>
            <option value="detailed">Detailed</option>
          </select>
          <button onClick={handleExtractAndSummarize} disabled={busy || !url}>
            {busy ? 'Processing...' : 'Extract & Summarize'}
          </button>
        </div>
        <div style={{ 
          background: 'Canvas', 
          border: '1px solid color-mix(in oklab, CanvasText 25%, transparent)', 
          borderRadius: '8px', 
          padding: '16px', 
          minHeight: '200px',
          fontFamily: 'inherit',
          fontSize: '14px',
          lineHeight: '1.6'
        }}>
          {summary ? (
            <ReactMarkdown
              components={{
                h1: ({children}) => <h1 style={{fontSize: '1.5em', marginBottom: '0.5em', marginTop: '0'}}>{children}</h1>,
                h2: ({children}) => <h2 style={{fontSize: '1.3em', marginBottom: '0.4em', marginTop: '1em'}}>{children}</h2>,
                h3: ({children}) => <h3 style={{fontSize: '1.1em', marginBottom: '0.3em', marginTop: '0.8em'}}>{children}</h3>,
                h4: ({children}) => <h4 style={{fontSize: '1em', marginBottom: '0.3em', marginTop: '0.6em', fontWeight: '600'}}>{children}</h4>,
                p: ({children}) => <p style={{marginBottom: '0.8em', marginTop: '0'}}>{children}</p>,
                ul: ({children}) => <ul style={{marginBottom: '0.8em', paddingLeft: '1.5em'}}>{children}</ul>,
                ol: ({children}) => <ol style={{marginBottom: '0.8em', paddingLeft: '1.5em'}}>{children}</ol>,
                li: ({children}) => <li style={{marginBottom: '0.3em'}}>{children}</li>,
                strong: ({children}) => <strong style={{fontWeight: '600'}}>{children}</strong>,
                em: ({children}) => <em style={{fontStyle: 'italic'}}>{children}</em>,
                code: ({children}) => <code style={{
                  background: 'color-mix(in oklab, CanvasText 10%, Canvas 90%)',
                  padding: '2px 4px',
                  borderRadius: '3px',
                  fontSize: '0.9em',
                  fontFamily: 'monospace'
                }}>{children}</code>,
                blockquote: ({children}) => <blockquote style={{
                  borderLeft: '3px solid color-mix(in oklab, CanvasText 30%, transparent)',
                  paddingLeft: '1em',
                  marginLeft: '0',
                  fontStyle: 'italic',
                  color: 'color-mix(in oklab, CanvasText 80%, transparent)'
                }}>{children}</blockquote>
              }}
            >
              {summary}
            </ReactMarkdown>
          ) : (
            <div style={{color: 'color-mix(in oklab, CanvasText 60%, transparent)'}}>
              Summary will appear here...
            </div>
          )}
        </div>
      </section>

      <section className="card">
        <h2>2) Ingest to Knowledge Base</h2>
        <button onClick={handleIngest} disabled={busy || !transcript}>Ingest</button>
      </section>

      <section className="card">
        <h2>3) Ask Questions (RAG)</h2>
        <div className="row">
          <input placeholder="Your question" value={question} onChange={e => setQuestion(e.target.value)} />
          <button onClick={handleAsk} disabled={busy || !question}>Ask</button>
        </div>
        {answer && (
          <div className="answer">
            <h3>Answer</h3>
            <div style={{ 
              background: 'color-mix(in oklab, Canvas 98%, CanvasText 0%)', 
              border: '1px solid color-mix(in oklab, CanvasText 15%, transparent)', 
              borderRadius: '8px', 
              padding: '16px', 
              marginBottom: '16px',
              lineHeight: '1.6'
            }}>
              <ReactMarkdown
                components={{
                  h1: ({children}) => <h1 style={{fontSize: '1.3em', marginBottom: '0.5em', marginTop: '0'}}>{children}</h1>,
                  h2: ({children}) => <h2 style={{fontSize: '1.2em', marginBottom: '0.4em', marginTop: '0.8em'}}>{children}</h2>,
                  h3: ({children}) => <h3 style={{fontSize: '1.1em', marginBottom: '0.3em', marginTop: '0.6em'}}>{children}</h3>,
                  p: ({children}) => <p style={{marginBottom: '0.6em', marginTop: '0'}}>{children}</p>,
                  ul: ({children}) => <ul style={{marginBottom: '0.6em', paddingLeft: '1.2em'}}>{children}</ul>,
                  ol: ({children}) => <ol style={{marginBottom: '0.6em', paddingLeft: '1.2em'}}>{children}</ol>,
                  li: ({children}) => <li style={{marginBottom: '0.2em'}}>{children}</li>,
                  strong: ({children}) => <strong style={{fontWeight: '600'}}>{children}</strong>,
                  em: ({children}) => <em style={{fontStyle: 'italic'}}>{children}</em>,
                  code: ({children}) => <code style={{
                    background: 'color-mix(in oklab, CanvasText 8%, Canvas 92%)',
                    padding: '1px 3px',
                    borderRadius: '2px',
                    fontSize: '0.9em',
                    fontFamily: 'monospace'
                  }}>{children}</code>
                }}
              >
                {answer}
              </ReactMarkdown>
            </div>
            <h4>Top Sources</h4>
            <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
              {sources.map((s, i) => (
                <div key={i} style={{ 
                  background: 'color-mix(in oklab, Canvas 96%, CanvasText 0%)', 
                  border: '1px solid color-mix(in oklab, CanvasText 10%, transparent)', 
                  borderRadius: '6px', 
                  padding: '12px', 
                  marginBottom: '8px',
                  fontSize: '13px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontWeight: '600' }}>
                    <span>Source #{i + 1}</span>
                    <span style={{ color: 'color-mix(in oklab, CanvasText 60%, transparent)' }}>
                      Score: {s.score.toFixed(3)}
                    </span>
                  </div>
                  {s.metadata && (
                    <div style={{ 
                      marginBottom: '8px', 
                      padding: '6px 8px', 
                      background: 'color-mix(in oklab, CanvasText 5%, Canvas 95%)',
                      borderRadius: '4px',
                      fontSize: '12px'
                    }}>
                      <div style={{ fontWeight: '600', marginBottom: '2px' }}>
                        📺 {s.metadata.video_title || 'Unknown Video'}
                      </div>
                      <div style={{ color: 'color-mix(in oklab, CanvasText 70%, transparent)' }}>
                        by {s.metadata.uploader || 'Unknown'} • 
                        <a 
                          href={s.metadata.video_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          style={{ 
                            color: 'color-mix(in oklab, blue 80%, CanvasText 20%)',
                            textDecoration: 'none',
                            marginLeft: '4px'
                          }}
                        >
                          Watch Video →
                        </a>
                      </div>
                    </div>
                  )}
                  <div style={{ 
                    lineHeight: '1.4',
                    color: 'color-mix(in oklab, CanvasText 80%, transparent)',
                    maxHeight: '100px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}>
                    {s.text.length > 200 ? s.text.substring(0, 200) + '...' : s.text}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  )
}

function chunkText(text: string, chunkSize: number): string[] {
  const words = text.split(/\s+/)
  const chunks: string[] = []
  let current: string[] = []
  for (const w of words) {
    current.push(w)
    if (current.join(' ').length > chunkSize) {
      chunks.push(current.join(' '))
      current = []
    }
  }
  if (current.length) chunks.push(current.join(' '))
  return chunks
}

function extractYouTubeId(input: string): string | null {
  if (!input) return null
  try {
    const url = new URL(input)
    if (url.hostname.includes('youtube.com')) {
      const v = url.searchParams.get('v')
      if (v && v.length === 11) return v
      const shorts = url.pathname.match(/\/shorts\/([\w-]{11})/)
      if (shorts) return shorts[1]
      const embed = url.pathname.match(/\/embed\/([\w-]{11})/)
      if (embed) return embed[1]
    }
    if (url.hostname === 'youtu.be') {
      const m = url.pathname.match(/\/([\w-]{11})/)
      if (m) return m[1]
    }
  } catch {
    const raw = input.match(/^([\w-]{11})$/)
    if (raw) return raw[1]
  }
  return null
}

function ApiHealth({ onResult }: { onResult: (ok: boolean) => void }) {
  useEffect(() => {
    let cancelled = false
    fetch(`${API_BASE}/health`, { method: 'GET' })
      .then(r => r.ok)
      .catch(() => false)
      .then(ok => { if (!cancelled) onResult(ok) })
    return () => { cancelled = true }
  }, [onResult])
  return null
}

