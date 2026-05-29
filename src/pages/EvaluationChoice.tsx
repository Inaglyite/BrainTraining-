import { useNavigate, Navigate } from 'react-router-dom'
import { getUser, updateFirstTestCompleted } from '../services/storage'

export default function EvaluationChoice() {
  const navigate = useNavigate()
  const user = getUser()
  
  // 如果已完成首测，直接跳转到/start
  if (user?.firstTestCompleted) {
    return <Navigate to="/start" replace />
  }

  function handleSkip() {
    updateFirstTestCompleted(true)
    navigate('/start')
  }

  function handleStart() {
    navigate('/games/suan-shi?firstTest=1')
  }

  return (
    <main className="container" style={{maxWidth: 600, textAlign: 'center', minHeight: '60vh', display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
      <div className="card" style={{padding: '50px 30px'}}>
        <div style={{width: 80, height: 80, background: 'rgba(139, 92, 246, 0.1)', color: '#8b5cf6', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px'}}>
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M12 8V12L15 15" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <h1 style={{fontSize: 28, marginBottom: 12}}>是否进行初始评估？</h1>
        <p className="meta" style={{marginBottom: 40, lineHeight: 1.6}}>
          初始评估将帮助我们了解您当前的基准水平。<br/>
          整个过程大约需要 1 分钟。您想现在开始吗？
        </p>

        <div style={{display: 'flex', gap: 16, justifyContent: 'center'}}>
          <button
            className="btn secondary"
            style={{padding: '12px 32px', fontSize: 16}}
            onClick={handleSkip}
          >
            跳过，直接开始
          </button>
          <button
            className="btn"
            style={{padding: '12px 32px', fontSize: 16, background: '#8b5cf6'}}
            onClick={handleStart}
          >
            开始评估
          </button>
        </div>
      </div>
    </main>
  )
}

