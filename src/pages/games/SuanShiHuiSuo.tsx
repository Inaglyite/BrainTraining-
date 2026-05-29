import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import CameraPreview from '../../components/CameraPreview.tsx'
import type { SessionState } from '../../types/api.ts'
import { createSession, getDailySummary, getSession, submitAction } from '../../services/gameApi.ts'
import { markFirstTestCompleted } from '../../services/authApi.ts'
import { ApiError } from '../../services/api.ts'
import { addTrainingDuration, getTrainingTotalSeconds, getUser, updateFirstTestCompleted } from '../../services/storage.ts'

export default function SuanShiHuiSuo() {
  const navigate = useNavigate()
  const [state, setState] = useState<SessionState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [gameStarted, setGameStarted] = useState(false)
  const [paused, setPaused] = useState(false)
  const [myAnswer, setMyAnswer] = useState<string | null>(null)
  const sessionIdRef = useRef<string | null>(null)
  const lastTriggerRef = useRef<number>(0)
  const [lastCorrect, setLastCorrect] = useState<boolean | null>(null)
  const firstTestMarkedRef = useRef(false)
  const completionHandledRef = useRef(false)
  const submitLockRef = useRef(false)
  const lastSubmitAtRef = useRef(0)
  const exitByChoiceRef = useRef(false)
  const [totalTrainingSeconds] = useState<number>(() => getTrainingTotalSeconds())
  const [pauseMenuOpen, setPauseMenuOpen] = useState(false)
  const timeoutSubmitLockRef = useRef(false)
  const autoSubmitAttemptRef = useRef<number>(-1)

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

  const updateStateSafely = (next: SessionState) => {
    setState((prev) => {
      if (!prev) return next
      if (next.attempt_index > prev.attempt_index) return next
      if (next.attempt_index < prev.attempt_index) return prev
      if (next.status === 'completed' && prev.status !== 'completed') return next
      if (next.elapsed_seconds >= prev.elapsed_seconds) return next
      return prev
    })
  }

  useEffect(() => {
    let mounted = true
    const user = getUser()
    createSession('suan-shi', 600, { userId: user?.userId ?? 'anonymous', difficultyLevel: 1.0 })
      .then((session) => {
        if (!mounted) return
        sessionIdRef.current = session.session_id
        updateStateSafely(session)
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
        const latest = await getSession('suan-shi', sessionIdRef.current as string)
        updateStateSafely(latest)
      } catch {
        // ignore polling errors to avoid interrupting current game
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
      const nums = ['1', '2', '3', '4', '5', '6', '7', '8', '9']
      if (!nums.includes(gesture)) return

      setMyAnswer(gesture)
      lastTriggerRef.current = now
    }

    window.addEventListener('camera_gesture', onCamera as EventListener)
    return () => window.removeEventListener('camera_gesture', onCamera as EventListener)
  }, [state, gameStarted, paused])

  const score = state?.score ?? 0
  const elapsed = state?.elapsed_seconds ?? 0
  const question = state?.current_question ?? '等待题目...'
  const nBack = state?.n_back_level ?? 1
  const totalQuestions = state?.suanshi_total_questions ?? 0
  const answeredQuestions = state?.suanshi_answered_questions ?? 0
  const canAnswer = state?.suanshi_can_answer ?? false
  const answerRemainingMs = state?.answer_remaining_ms ?? null
  const currentAttempt = state?.attempt_index ?? -1
  const stateStatus = state?.status
  const stateCanAnswer = state?.suanshi_can_answer ?? false
  // 以服务端状态为准，避免前端派生进度导致提前结束
  const isCompleted = stateStatus === 'completed'
  const isActive = stateStatus === 'active'
  const isFirstTest = new URLSearchParams(window.location.search).get('firstTest') === '1'
  const displayedTotalTrainingSeconds = totalTrainingSeconds + (gameStarted && !isCompleted ? elapsed : 0)

  useEffect(() => {
    if (!sessionIdRef.current || !gameStarted || paused || !state) return
    if (state.status !== 'active' || !canAnswer) return
    if (answerRemainingMs === null) return
    if (autoSubmitAttemptRef.current === currentAttempt) return

    const runAutoSubmit = async () => {
      if (!sessionIdRef.current || submitLockRef.current || timeoutSubmitLockRef.current) return
      autoSubmitAttemptRef.current = currentAttempt
      timeoutSubmitLockRef.current = true
      try {
        const autoAnswer = myAnswer ?? '0'
        const result = await submitAction('suan-shi', sessionIdRef.current, autoAnswer)
        setLastCorrect(result.correct)
        updateStateSafely(result.state)
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
  }, [answerRemainingMs, canAnswer, currentAttempt, gameStarted, paused, state, myAnswer])

  // ...existing code...

  useEffect(() => {
    if (!sessionIdRef.current || !gameStarted || paused) return
    if (!stateStatus || stateStatus === 'completed' || stateCanAnswer) return

    const timer = window.setTimeout(async () => {
      if (!sessionIdRef.current || submitLockRef.current) return
      submitLockRef.current = true
      try {
        const result = await submitAction('suan-shi', sessionIdRef.current, '1')
        updateStateSafely(result.state)
        setLastCorrect(null)
        setMyAnswer(null)
        setError(null)
      } catch (err) {
        const message = err instanceof ApiError ? err.message : '自动跳过热身题失败'
        setError(message)
      } finally {
        submitLockRef.current = false
      }
    }, 700)

    return () => window.clearTimeout(timer)
  }, [state?.attempt_index, stateCanAnswer, stateStatus, gameStarted, paused])

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
            const result = await submitAction('suan-shi', sessionIdRef.current, myAnswer)
            setLastCorrect(result.correct)
            updateStateSafely(result.state)
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

  useEffect(() => {
    async function syncFirstTest() {
      if (!state || answeredQuestions < totalQuestions) return
      if (!isFirstTest || firstTestMarkedRef.current) return

      const user = getUser()
      if (!user || user.firstTestCompleted) return

      firstTestMarkedRef.current = true
      try {
        await markFirstTestCompleted(user.userId)
        updateFirstTestCompleted(true)
      } catch {
        firstTestMarkedRef.current = false
      }
    }
    
    // 游戏完成：题目全部完成后立即跳转到结果页面
    if (isCompleted && answeredQuestions > 0 && state && !completionHandledRef.current) {
      completionHandledRef.current = true
      void (async () => {
        const score = Math.max(0, state.score ?? 0)
        const accuracy = Math.min(1, Math.max(0, score / (Math.max(1, answeredQuestions) * 10)))
        const newTotalTrainingSeconds = addTrainingDuration(elapsed)
        const user = getUser()
        let todayRemainingRounds: number | null = null
        if (user?.userId) {
          try {
            const dailySummary = await getDailySummary(user.userId)
            todayRemainingRounds = dailySummary.shu_xiang_remaining_rounds
          } catch {
            todayRemainingRounds = null
          }
        }

        await syncFirstTest()

        // 立即跳转，不需要延迟
        await exitFullscreen()
        navigate('/difficulty-result', {
          state: {
            accuracy,
            nBackLevel: nBack,
            gameName: '算式回溯',
            gameDuration: elapsed,
            totalTrainingSeconds: newTotalTrainingSeconds,
            todayRemainingRounds,
            recommendation: state.difficulty_recommendation,
          }
        })
      })()
      return () => {}
    }
  }, [answeredQuestions, elapsed, isCompleted, isFirstTest, navigate, nBack, state, totalQuestions])

  return (
    <div className="game-container">
      <div className="left-info-panel">
        <div className="info-card">
          <div className="info-card-label">用时</div>
          <div className="info-card-value" style={{color: 'var(--text-h)'}}>
            {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, '0')}
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

        <div className="camera-simple">
          <CameraPreview cornerMode={true} />
        </div>

        <div className="info-card">
          <div className="info-card-label">进度</div>
          <div className="info-card-value" style={{ fontSize: 24 }}>
            {answeredQuestions}/{totalQuestions}
          </div>
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
        ) : isActive ? (
          <>
            <div style={{ fontSize: 20, color: 'var(--muted)', marginBottom: 16, textAlign: 'center' }}>
              请用手势数字回答 {canAnswer ? `前${nBack}题答案` : '正在热身记忆...'}
            </div>
            <div className="big-equation">{question}</div>
            <div style={{ marginTop: 16, fontSize: 22, fontWeight: 700, color: 'var(--text-h)' }}>
              {canAnswer ? '请直接比出答案手势 (1-9)' : '提示：前几轮不计分，仅用于建立记忆队列'}
            </div>
            {canAnswer && answerRemainingMs !== null && (
              <div style={{ marginTop: 8, fontSize: 16, color: answerRemainingMs <= 1000 ? '#ef4444' : 'var(--muted)' }}>
                本题剩余: {(answerRemainingMs / 1000).toFixed(1)} 秒
              </div>
            )}
            {lastCorrect !== null && canAnswer && (
              <div style={{ marginTop: 12, fontSize: 28, fontWeight: 700, color: lastCorrect ? '#10b981' : '#ef4444' }}>
                {lastCorrect ? '回答正确' : '回答错误'}
              </div>
            )}
          </>
        ) : (
          <div className="big-equation" style={{background: '#10b981', WebkitTextFillColor: 'transparent', WebkitBackgroundClip: 'text'}}>
            完成！
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
