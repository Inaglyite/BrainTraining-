import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import CameraPreview from '../../components/CameraPreview.tsx'
import type { SessionState } from '../../types/api.ts'
import { createSession, getDailySummary, getSession, getSessionInteractions, submitAction } from '../../services/gameApi.ts'
import { ApiError } from '../../services/api.ts'
import { addTrainingDuration, getTrainingTotalSeconds, getUser } from '../../services/storage.ts'

import rockImg from '../../assets/images/rock.png'
import paperImg from '../../assets/images/paper.png'
import scissorsImg from '../../assets/images/scissors.png'

const choiceImgs: Record<string, string> = {
  rock: rockImg,
  paper: paperImg,
  scissors: scissorsImg
}

const instructionMeta = {
  win: { text: '请胜利', color: '#10b981', hint: '出拳后要赢过电脑' },
  lose: { text: '请失败', color: '#ef4444', hint: '出拳后要输给电脑' },
  draw: { text: '请平局', color: '#6366f1', hint: '出和电脑相同的手势' }
} as const

export default function RPS() {
  const navigate = useNavigate()
  const [state, setState] = useState<SessionState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [gameStarted, setGameStarted] = useState(false)
  const [paused, setPaused] = useState(false)
  const [myAction, setMyAction] = useState<string | null>(null)
  const sessionIdRef = useRef<string | null>(null)
  const lastTriggerRef = useRef<number>(0)
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
  
  const [lastCorrect, setLastCorrect] = useState<boolean | null>(null)
  const [lastUserAction, setLastUserAction] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    const user = getUser()
    createSession('rps', 60, { userId: user?.userId ?? 'anonymous', difficultyLevel: 1.0 })
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
        const latest = await getSession('rps', sessionIdRef.current as string)
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
      
      const valid = ['rock', 'paper', 'scissors']
      if (!valid.includes(gesture)) return

      setMyAction(gesture)
      setLastUserAction(gesture)
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
        if (myAction !== null && !paused && gameStarted && sessionIdRef.current) {
          if (myAction === null || !sessionIdRef.current) return
          try {
            submitLockRef.current = true
            lastSubmitAtRef.current = now
            const result = await submitAction('rps', sessionIdRef.current, myAction)
            setLastCorrect(result.correct)
            setState(result.state)
            setMyAction(null)
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
  }, [myAction, paused, gameStarted])

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

  const score = state?.score ?? 0
  const elapsed = state?.elapsed_seconds ?? 0
  const timeLeft = state?.remaining_seconds ?? 60
  const answerRemainingMs = state?.answer_remaining_ms ?? null
  const currentAttempt = state?.attempt_index ?? -1
  const displayedTotalTrainingSeconds = totalTrainingSeconds + (gameStarted && timeLeft > 0 ? elapsed : 0)
  const cpuChoice = state?.rps_cpu_action
  const pInst = state?.rps_instruction
  const currentInstruction = pInst ? instructionMeta[pInst] : null

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
        const autoAction = myAction ?? lastUserAction ?? 'rock'
        const result = await submitAction('rps', sessionIdRef.current, autoAction)
        setLastCorrect(result.correct)
        setState(result.state)
        setMyAction(null)
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
  }, [answerRemainingMs, currentAttempt, gameStarted, paused, state, myAction, lastUserAction])

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
        const rows = await getSessionInteractions('rps', completedState.session_id, 2000)
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
          gameName: '石头剪刀布',
          gameDuration: elapsedSeconds,
          totalTrainingSeconds: next,
          todayRemainingRounds,
          recommendation: completedState.difficulty_recommendation,
        },
      })
    }

    void handleCompleted()
  }, [navigate, state])

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
          <div className="info-card-label">本题剩余</div>
          <div className="info-card-value" style={{ color: (answerRemainingMs ?? 0) <= 1000 ? '#ef4444' : 'var(--text-h)' }}>
            {answerRemainingMs === null ? '-' : `${(answerRemainingMs / 1000).toFixed(1)}s`}
          </div>
        </div>

        <div className="camera-simple">
          <CameraPreview cornerMode={true} detectionMode="rps" />
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

        {lastUserAction !== null && gameStarted && !paused && (
          <div style={{
            textAlign: 'center',
            padding: '12px',
            background: 'rgba(239, 143, 52, 0.18)',
            borderRadius: '8px',
            color: '#6b451b',
            fontSize: 14,
            fontWeight: 600
          }}>
            按空格键确认动作
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
          <>
            {currentInstruction && (
              <div style={{ textAlign: 'center', marginBottom: 20 }}>
                <div style={{ fontSize: 36, fontWeight: 'bold', color: currentInstruction.color, marginBottom: 8 }}>
                  {currentInstruction.text}
                </div>
                <div style={{ fontSize: 18, color: 'var(--muted)' }}>
                  {currentInstruction.hint}
                </div>
              </div>
            )}
            
            <div className="rps-choices" style={{marginTop: 0}}>
              <div className="rps-choice rps-cpu">
                <h3>电脑</h3>
                {cpuChoice ? <img src={choiceImgs[cpuChoice]} alt={cpuChoice} /> : <div style={{width:140, height:140, display:'flex', alignItems:'center', justifyContent:'center', border:'2px dashed var(--border)', borderRadius:16, color:'var(--muted)'}}>准备中...</div>}
              </div>
              
              <div className="rps-vs">VS</div>
              
              <div className="rps-choice">
                <h3>你</h3>
                {lastUserAction ? <img src={choiceImgs[lastUserAction]} alt={lastUserAction} /> : <div style={{width:140, height:140, display:'flex', alignItems:'center', justifyContent:'center', border:'2px dashed var(--border)', borderRadius:16, color:'var(--muted)'}}>请出拳</div>}
              </div>
            </div>

            <div style={{minHeight: '60px', marginTop: 32, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
              {lastCorrect !== null && (
                <div style={{fontSize: 32, fontWeight: 'bold', color: lastCorrect ? '#10b981' : '#ef4444'}}>
                   {lastCorrect ? '太棒了 🎉' : '哎呀，错了 💔'}
                </div>
              )}
            </div>
          </>
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
