import { useEffect, useState } from 'react'
import { ApiError } from '../services/api.ts'
import { getAIAnalysis, getPeriodSummary } from '../services/gameApi.ts'
import { getUser } from '../services/storage.ts'
import type { PeriodSummaryResponse, SummaryPeriod } from '../types/api.ts'
import AgentChat from '../components/AgentChat.tsx'

export default function Reports(){
  const user = getUser()
  const userId = user?.userId ?? null
  const [period, setPeriod] = useState<SummaryPeriod>('daily')
  const [anchorDate, setAnchorDate] = useState(() => new Date().toISOString().slice(0, 10))
  const [summary, setSummary] = useState<PeriodSummaryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [aiAnalysis, setAiAnalysis] = useState<string | null>(null)
  const [aiLoading, setAiLoading] = useState(false)
  const [aiError, setAiError] = useState<string | null>(null)

  useEffect(() => {
    if (!userId) return

    const currentUserId = userId
    let cancelled = false
    async function loadSummary() {
      setLoading(true)
      setError(null)
      try {
        const resp = await getPeriodSummary(currentUserId, period, anchorDate)
        if (cancelled) return
        setSummary(resp)
      } catch (e) {
        if (cancelled) return
        const message = e instanceof ApiError ? e.message : '获取报告失败'
        setError(message)
        setSummary(null)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void loadSummary()

    return () => {
      cancelled = true
    }
  }, [userId, period, anchorDate])

  async function handleAIAnalysis() {
    if (!userId) return
    setAiLoading(true)
    setAiError(null)
    setAiAnalysis(null)
    try {
      const resp = await getAIAnalysis(userId, period, anchorDate)
      setAiAnalysis(resp.analysis_text)
    } catch (e) {
      const message = e instanceof ApiError ? e.message : 'AI 分析请求失败'
      setAiError(message)
    } finally {
      setAiLoading(false)
    }
  }

  function handleExport(){
    if (!summary) return
    const blob = new Blob([JSON.stringify(summary, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${summary.period}-summary-${summary.anchor_date}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  function formatDuration(seconds: number){
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${String(secs).padStart(2, '0')}`
  }

  return (
    <main className="card">
      <h1>锻炼报告</h1>
      <p className="meta">用户：{userId || '未注册'}</p>
      <div style={{display:'flex', gap:8, alignItems:'center', marginTop:12, flexWrap: 'wrap'}}>
        <label className="meta">周期</label>
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value as SummaryPeriod)}
          style={{padding:'8px 10px', borderRadius:8, border:'1px solid var(--border)'}}
        >
          <option value="daily">日报</option>
          <option value="monthly">月报</option>
          <option value="quarterly">季报</option>
        </select>
        <label className="meta">锚点日期</label>
        <input
          type="date"
          value={anchorDate}
          onChange={(e) => setAnchorDate(e.target.value)}
          style={{padding:'8px 10px', borderRadius:8, border:'1px solid var(--border)'}}
        />
        <div style={{marginLeft:'auto'}}>
          <button className="btn secondary" onClick={handleExport} disabled={!summary}>导出 JSON</button>
        </div>
      </div>

      {loading && <p className="meta" style={{marginTop: 16}}>加载中...</p>}
      {error && <p className="meta" style={{marginTop: 16, color: '#ef4444'}}>{error}</p>}

      {userId && summary && (
        <>
          <div className="info-card" style={{marginTop: 14}}>
            <div className="info-card-label">自动生成总结</div>
            <div className="meta" style={{marginTop: 8, color: 'var(--text)'}}>{summary.report_text}</div>
          </div>

          <div style={{display:'grid', gridTemplateColumns:'repeat(2, minmax(160px, 1fr))', gap:12, marginTop:16}}>
            <div className="info-card"><div className="info-card-label">统计区间</div><div className="info-card-value" style={{fontSize: 18}}>{summary.period_start} ~ {summary.period_end}</div></div>
            <div className="info-card"><div className="info-card-label">总时长</div><div className="info-card-value">{formatDuration(summary.total_duration_seconds)}</div></div>
            <div className="info-card"><div className="info-card-label">总局数</div><div className="info-card-value">{summary.total_sessions}</div></div>
            <div className="info-card"><div className="info-card-label">平均正确率</div><div className="info-card-value">{typeof summary.average_accuracy === 'number' ? `${Math.round(summary.average_accuracy * 100)}%` : '-'}</div></div>
            <div className="info-card"><div className="info-card-label">算式回溯</div><div className="info-card-value">{summary.suan_shi_sessions}</div></div>
            <div className="info-card"><div className="info-card-label">数箱子</div><div className="info-card-value">{summary.shu_xiang_sessions}</div></div>
            <div className="info-card"><div className="info-card-label">指令石头剪刀布</div><div className="info-card-value">{summary.rps_sessions}</div></div>
          </div>

          <div style={{marginTop: 24, borderTop: '1px solid var(--border)', paddingTop: 16}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12}}>
              <h2 style={{margin: 0}}>AI 智能分析</h2>
              <button
                className="btn secondary"
                onClick={handleAIAnalysis}
                disabled={aiLoading || !summary}
                style={{padding: '8px 16px', fontSize: 14}}
              >
                {aiLoading ? '分析中...' : aiAnalysis ? '重新分析' : '获取AI分析'}
              </button>
            </div>

            {aiError && (
              <div className="info-card" style={{borderColor: '#ef4444', background: '#fef2f2'}}>
                <p className="meta" style={{color: '#ef4444', margin: 0}}>{aiError}</p>
              </div>
            )}

            {aiLoading && (
              <div className="info-card">
                <p className="meta" style={{margin: 0}}>AI 正在分析您的训练数据，请稍候...</p>
              </div>
            )}

            {aiAnalysis && !aiLoading && (
              <div className="info-card" style={{whiteSpace: 'pre-wrap', lineHeight: 1.7}}>
                <div style={{fontSize: 14, color: 'var(--text)'}}
                  dangerouslySetInnerHTML={{
                    __html: aiAnalysis
                      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                      .replace(/\n/g, '<br/>')
                  }}
                />
              </div>
            )}
          </div>

          {userId && <AgentChat userId={userId} />}
        </>
      )}
    </main>
  )
}
