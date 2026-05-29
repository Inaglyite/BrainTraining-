import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import CameraPreview from '../../components/CameraPreview.tsx'
import boxImg from '../../assets/images/Box.png'
import type { SessionState } from '../../types/api.ts'
import { createSession, getDailySummary, getSession, getSessionInteractions, submitAction } from '../../services/gameApi.ts'
import { ApiError } from '../../services/api.ts'
import { addTrainingDuration, getTrainingTotalSeconds, getUser } from '../../services/storage.ts'

export default function ShuXiangZi() {
  const navigate = useNavigate()
  const [state, setState] = useState<SessionState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [gameStarted, setGameStarted] = useState(false)
  const [paused, setPaused] = useState(false)
  const [myAnswer, setMyAnswer] = useState<number | null>(null)
  const lastTriggerRef = useRef<number>(0)
  const sessionIdRef = useRef<string | null>(null)
  const completionHandledRef = useRef(false)
  const exitByChoiceRef = useRef(false)
  const submitLockRef = useRef(false)
  const timeoutSubmitLockRef = useRef(false)
  const lastSubmitAtRef = useRef(0)
  const autoSubmitAttemptRef = useRef<number>(-1)
  const [totalTrainingSeconds, setTotalTrainingSeconds] = useState<number>(() => getTrainingTotalSeconds())
  const [pauseMenuOpen, setPauseMenuOpen] = useState(false)

  const requestFullscreen = async () => {
    if (document.fullscreenElement) return
    try {
      await document.documentElement.requestFullscreen()
    } catch {
      // Ignore environments where fullscreen is unavailable.
    }
  }

  const exitFullscreen = async () => {
    if (!document.fullscreenElement) return
    try {
      await document.exitFullscreen()
    } catch {
      // Ignore fullscreen exit failures.
    }
  }

  const handleStartGame = async () => {
    setGameStarted(true)
    setPaused(false)
    setPauseMenuOpen(false)
    exitByChoiceRef.current = false
    await requestFullscreen()
  }

  const handleExitToCover = async () => {
    exitByChoiceRef.current = true
    await exitFullscreen()
    navigate('/')
  }

  const handleRestart = async () => {
    exitByChoiceRef.current = true
    await exitFullscreen()
    navigate(0)
  }

  useEffect(() => {
    let mounted = true
    const user = getUser()
    createSession('shu-xiang', 60, { userId: user?.userId ?? 'anonymous', difficultyLevel: 1.0 })
      .then((session) => {
        if (!mounted) return
        sessionIdRef.current = session.session_id
        setState(session)
      })
      .catch((e) => {
        const message = e instanceof ApiError ? e.message : '创建游戏会话失败'
        setError(message)
      })
      .finally(() => setLoading(false))

    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    if (!sessionIdRef.current || !gameStarted || paused) return
    const timer = setInterval(async () => {
      try {
        const latest = await getSession('shu-xiang', sessionIdRef.current as string)
        setState(latest)
      } catch {
        // ignore intermittent polling errors
      }
    }, 1000)

    return () => clearInterval(timer)
  }, [state?.session_id, gameStarted, paused])

  useEffect(() => {
    async function onCamera(e: Event) {
      const ev = e as CustomEvent<{ gesture?: string }>
      const gesture = ev.detail?.gesture
      if (!gesture || !sessionIdRef.current || !gameStarted) return
      if (!state || state.status === 'completed' || paused) return

      const now = Date.now()
      if (now - lastTriggerRef.current < 300) return
      
      const nums = ['1','2','3','4','5','6','7','8','9']
      if (!nums.includes(gesture)) return

      setMyAnswer(parseInt(gesture))
      lastTriggerRef.current = now
    }

    window.addEventListener('camera_gesture', onCamera as EventListener)
    return () => window.removeEventListener('camera_gesture', onCamera as EventListener)
  }, [state, gameStarted, paused])

  // ...existing code...

  useEffect(() => {
    const onKeyDown = async (e: KeyboardEvent) => {
      if (e.key === 'Escape' && gameStarted) {
        e.preventDefault()
        setPaused(true)
        setPauseMenuOpen(true)
        return
      }

      if (e.code === 'Space') {
        e.preventDefault()
        if (e.repeat || submitLockRef.current) return
        const now = Date.now()
        if (now - lastSubmitAtRef.current < 500) return
        if (myAnswer !== null && !paused && gameStarted && sessionIdRef.current) {
          if (myAnswer === null || !sessionIdRef.current) return
          try {
            submitLockRef.current = true
            lastSubmitAtRef.current = now
            const result = await submitAction('shu-xiang', sessionIdRef.current, myAnswer.toString())
            setState(result.state)
            setMyAnswer(null)
            setError(null)
          } catch (err) {
            const message = err instanceof ApiError ? err.message : '提交动作失败'
            setError(message)
          } finally {
            submitLockRef.current = false
          }
        }
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [myAnswer, paused, gameStarted])

  useEffect(() => {
    if (!gameStarted) return

    const onFullscreenChange = () => {
      if (!document.fullscreenElement && !exitByChoiceRef.current) {
        setPaused(true)
        setPauseMenuOpen(true)
      }
    }

    document.addEventListener('fullscreenchange', onFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', onFullscreenChange)
  }, [gameStarted])

  const timeLeft = state?.remaining_seconds ?? 60
  const elapsed = state?.elapsed_seconds ?? 0
  const score = state?.score ?? 0
  const boxCount = state?.box_count ?? 0
  const answerRemainingMs = state?.answer_remaining_ms ?? null
  const currentAttempt = state?.attempt_index ?? -1
  const displayedTotalTrainingSeconds = totalTrainingSeconds + (gameStarted && timeLeft > 0 ? elapsed : 0)

  useEffect(() => {
    if (!sessionIdRef.current || !gameStarted || paused || !state) return
    if (state.status !== 'active') return
    if (answerRemainingMs === null) return
    if (autoSubmitAttemptRef.current === currentAttempt) return

    const runAutoSubmit = async () => {
      if (!sessionIdRef.current || submitLockRef.current || timeoutSubmitLockRef.current) return
      autoSubmitAttemptRef.current = currentAttempt
      timeoutSubmitLockRef.current = true
      try {
        const autoAnswer = myAnswer !== null ? myAnswer.toString() : '0'
        const result = await submitAction('shu-xiang', sessionIdRef.current, autoAnswer)
        setState(result.state)
        setMyAnswer(null)
        setError(null)
      } catch (err) {
        autoSubmitAttemptRef.current = -1
        const message = err instanceof ApiError ? err.message : '超时自动提交失败'
        setError(message)
      } finally {
        timeoutSubmitLockRef.current = false
      }
    }

    if (answerRemainingMs <= 0) {
      void runAutoSubmit()
      return
    }

    const timer = window.setTimeout(() => {
      void runAutoSubmit()
    }, Math.max(0, answerRemainingMs - 30))

    return () => window.clearTimeout(timer)
  }, [answerRemainingMs, currentAttempt, gameStarted, paused, state, myAnswer])

  useEffect(() => {
    if (!state || state.status !== 'completed' || completionHandledRef.current) return
    completionHandledRef.current = true
    const completedState = state

    async function handleCompleted() {
      const elapsedSeconds = completedState.elapsed_seconds ?? 0
      const next = addTrainingDuration(elapsedSeconds)
      setTotalTrainingSeconds(next)

      let accuracy = 0
      try {
        const rows = await getSessionInteractions('shu-xiang', completedState.session_id, 2000)
        const attempts = rows.length
        const correct = rows.filter((r) => r.correct).length
        accuracy = attempts > 0 ? correct / attempts : 0
      } catch {
        accuracy = 0
      }

      let todayRemainingRounds: number | null = null
      const user = getUser()
      if (user?.userId) {
        try {
          const dailySummary = await getDailySummary(user.userId)
          todayRemainingRounds = dailySummary.shu_xiang_remaining_rounds
        } catch {
          todayRemainingRounds = null
        }
      }

      await exitFullscreen()
      navigate('/difficulty-result', {
        state: {
          accuracy,
          nBackLevel: 0,
          gameName: '数箱子',
          gameDuration: elapsedSeconds,
          totalTrainingSeconds: next,
          todayRemainingRounds,
          recommendation: completedState.difficulty_recommendation,
        },
      })
    }

    void handleCompleted()
  }, [navigate, state])
  
  const difficultyLevel = state?.difficulty_level ?? 1
  const useDenseLayout = difficultyLevel >= 4
  const renderBoxes = React.useMemo(() => {
    const total = Math.max(0, boxCount)
    if (!useDenseLayout) {
      return Array.from({ length: total }).map((_, i) => ({
        key: i,
        left: '0%',
        top: '0%',
        scale: 1,
        rotate: 0,
        zIndex: 1,
      }))
    }

    const overlapStrength = Math.min(0.45, Math.max(0.0, (difficultyLevel - 4) * 0.08))
    return Array.from({ length: total }).map((_, i) => {
      const baseLeft = 12 + (Math.random() * 76)
      const baseTop = 10 + (Math.random() * 72)
      const overlapOffset = (Math.random() - 0.5) * 100 * overlapStrength
      const scale = 0.95 + Math.random() * 0.25
      const rotate = (Math.random() - 0.5) * 24
      return {
        key: i,
        left: `${Math.min(88, Math.max(4, baseLeft + overlapOffset))}%`,
        top: `${Math.min(86, Math.max(4, baseTop + overlapOffset))}%`,
        scale,
        rotate,
        zIndex: Math.floor(Math.random() * 20),
      }
    })
  }, [boxCount, difficultyLevel, state?.attempt_index, useDenseLayout])

  return (
    <div className="game-container">
      <div className="left-info-panel">
        <div className="info-card">
          <div className="info-card-label">倒计时</div>
          <div className="info-card-value" style={{color: timeLeft <= 10 ? '#ef4444' : 'var(--text-h)'}}>
            {Math.floor(timeLeft / 60)}:{String(timeLeft % 60).padStart(2, '0')}
          </div>
        </div>

        <div className="info-card">
          <div className="info-card-label">累计训练时长</div>
          <div className="info-card-value" style={{ color: 'var(--text-h)', fontSize: 22 }}>
            {Math.floor(displayedTotalTrainingSeconds / 60)}:{String(displayedTotalTrainingSeconds % 60).padStart(2, '0')}
          </div>
        </div>

        <div className="info-card">
          <div className="info-card-label">分数</div>
          <div className="info-card-value" style={{color: 'var(--accent)'}}>
            {score}
          </div>
        </div>

        <div className="info-card">
          <div className="info-card-label">我的答案</div>
          <div className="info-card-value">
            {myAnswer === null ? '-' : myAnswer}
          </div>
        </div>

        <div className="info-card">
          <div className="info-card-label">本题剩余</div>
          <div className="info-card-value" style={{ color: (answerRemainingMs ?? 0) <= 1000 ? '#ef4444' : 'var(--text-h)' }}>
            {answerRemainingMs === null ? '-' : `${(answerRemainingMs / 1000).toFixed(1)}s`}
          </div>
        </div>

        <div className="camera-simple">
          <CameraPreview cornerMode={true} />
        </div>

        <div style={{display: 'flex', gap: 8, justifyContent: 'center', alignItems: 'center', minHeight: 50}}>
          <button 
            className="btn secondary"
            style={{flex: 1}}
            onClick={() => setPaused(!paused)}
            disabled={!gameStarted}
          >
            {paused ? '继续' : '暂停'}
          </button>
        </div>

        {myAnswer !== null && gameStarted && !paused && (
          <div style={{
            textAlign: 'center',
            padding: '12px',
            background: 'rgba(239, 143, 52, 0.18)',
            borderRadius: '8px',
            color: '#6b451b',
            fontSize: 14,
            fontWeight: 600
          }}>
            按空格键确认答案
          </div>
        )}
      </div>

      <div className="main-game-area">
        {loading ? (
          <div className="big-equation">加载中...</div>
        ) : error ? (
          <div className="big-equation" style={{ fontSize: 28, letterSpacing: 1 }}>{error}</div>
        ) : !gameStarted ? (
          <div style={{textAlign: 'center'}}>
            <div className="big-equation" style={{marginBottom: 40}}>准备好了吗？</div>
            <button className="btn" style={{padding: '16px 48px', fontSize: 18}} onClick={handleStartGame}>
              开始游戏
            </button>
          </div>
        ) : timeLeft > 0 ? (
          <div className="boxes-area" style={useDenseLayout ? { position: 'relative', minHeight: 420 } : undefined}>
            {boxCount === 0 || boxCount === null ? (
              <div style={{opacity:0.5, fontSize:24, textAlign: 'center'}}>准备中...请比划屏幕上箱子的数量 (1-9)</div>
            ) : renderBoxes.map((_, i)=>(
              <div key={i} className="box-item" style={useDenseLayout ? {
                position: 'absolute',
                left: renderBoxes[i].left,
                top: renderBoxes[i].top,
                transform: `translate(-50%, -50%) scale(${renderBoxes[i].scale}) rotate(${renderBoxes[i].rotate}deg)`,
                margin: 0,
                zIndex: renderBoxes[i].zIndex,
              } : {
                transform: 'scale(1)',
                margin: '10px'
              }}>
                <img src={boxImg} alt="box" />
              </div>
            ))}
          </div>
        ) : (
          <div className="big-equation" style={{background: '#10b981', WebkitTextFillColor: 'transparent', WebkitBackgroundClip: 'text'}}>
            时间到!
          </div>
        )}
      </div>

      {pauseMenuOpen && (
        <div className="pause-overlay">
          <div className="pause-card">
            <h2>游戏已暂停</h2>
            <p className="meta">按 ESC 会打开这个菜单，不会直接退出当前游戏。</p>
            <div className="pause-actions">
              <button
                className="btn"
                onClick={async () => {
                  setPauseMenuOpen(false)
                  setPaused(false)
                  await requestFullscreen()
                }}
              >
                继续
              </button>
              <button className="btn secondary" onClick={handleRestart}>重开</button>
              <button className="btn secondary" onClick={handleExitToCover}>退出</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
