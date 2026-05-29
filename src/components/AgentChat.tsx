import { useState, useRef, useEffect } from 'react'
import { sendAgentMessage } from '../services/gameApi'
import { ApiError } from '../services/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface Props {
  userId: string
}

export default function AgentChat({ userId }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function handleSend() {
    const text = input.trim()
    if (!text || loading) return

    setInput('')
    setError(null)
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)

    try {
      const resp = await sendAgentMessage(userId, text)
      setMessages(prev => [...prev, { role: 'assistant', content: resp.reply }])
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : '发送失败'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div style={{
      border: '1px solid var(--border)',
      borderRadius: 12,
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column',
      height: 400,
      marginTop: 16,
    }}>
      <div style={{
        padding: '10px 16px',
        borderBottom: '1px solid var(--border)',
        fontWeight: 600,
        fontSize: 14,
        background: 'var(--bg)',
      }}>
        Dr. Brain 智能助手
      </div>

      <div style={{
        flex: 1,
        overflow: 'auto',
        padding: 16,
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
      }}>
        {messages.length === 0 && (
          <p className="meta" style={{ textAlign: 'center', marginTop: 40 }}>
            向我提问你的训练情况吧！例如"我最近表现怎么样？"或"给我一些训练建议"
          </p>
        )}

        {messages.map((m, i) => (
          <div key={i} style={{
            alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '80%',
            padding: '8px 14px',
            borderRadius: 16,
            fontSize: 14,
            lineHeight: 1.5,
            background: m.role === 'user' ? 'var(--primary)' : 'var(--bg)',
            color: m.role === 'user' ? '#fff' : 'var(--text)',
            border: m.role === 'assistant' ? '1px solid var(--border)' : 'none',
          }}>
            {m.content}
          </div>
        ))}

        {loading && (
          <div style={{ alignSelf: 'flex-start', padding: '8px 14px', fontSize: 14, color: 'var(--text-muted)' }}>
            Dr. Brain 正在思考...
          </div>
        )}

        {error && (
          <div style={{ alignSelf: 'center', padding: '6px 12px', fontSize: 13, color: '#ef4444', background: '#fef2f2', borderRadius: 8 }}>
            {error}
          </div>
        )}

        <div ref={endRef} />
      </div>

      <div style={{
        padding: '10px 16px',
        borderTop: '1px solid var(--border)',
        display: 'flex',
        gap: 8,
      }}>
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入你的问题..."
          disabled={loading}
          style={{
            flex: 1,
            padding: '8px 12px',
            borderRadius: 20,
            border: '1px solid var(--border)',
            fontSize: 14,
            outline: 'none',
          }}
        />
        <button
          className="btn"
          onClick={handleSend}
          disabled={loading || !input.trim()}
          style={{ padding: '8px 18px', borderRadius: 20, fontSize: 14 }}
        >
          发送
        </button>
      </div>
    </div>
  )
}
