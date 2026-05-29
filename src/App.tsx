import './App.css'
import type { ReactElement } from 'react'
import { useState } from 'react'
import { BrowserRouter, Routes, Route, Link, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { getUser } from './services/storage'
import GameCover from './pages/GameCover'
import Login from './pages/Login'
import Registration from './pages/Registration'
import RoleSelect from './pages/RoleSelect'
import EvaluationChoice from './pages/EvaluationChoice'
import Onboarding from './pages/Onboarding'
import Start from './pages/Start'
import DifficultyResult from './pages/DifficultyResult'
import SuanShiHuiSuo from './pages/games/SuanShiHuiSuo'
import ShuXiangZi from './pages/games/ShuXiangZi'
import RPS from './pages/games/RPS'
import Reports from './pages/Reports'
import Profile from './pages/Profile'
import { PresentationProvider } from './contexts/presentation'
import DoctorResearching from './assets/images/Dr_Brain_Image/Doctor_researching.png'

function Header(){
  const navigate = useNavigate()
  const user = getUser()

  return (
    <header className="app-header">
      <div className="brand">手势训练原型</div>
      {user ? (
        <>
          <Link to="/start" className="nav-link">首页</Link>
          <button 
            className="nav-link" 
            style={{background: 'none', border: 'none', cursor: 'pointer', color: 'var(--ink-800)'}}
            onClick={() => navigate('/profile')}
          >
            {user.userId}
          </button>
        </>
      ) : (
        <>
          <Link to="/login" className="nav-link">登录</Link>
          <Link to="/register" className="nav-link">注册</Link>
        </>
      )}
      <div style={{marginLeft: 'auto', display:'flex', gap:8, alignItems:'center'}}>
        {/* Exit button: go back to previous page, fallback to /start */}
        <button className="btn secondary" onClick={() => { if ((window.history?.length ?? 0) > 1) navigate(-1); else navigate('/start') }}>退出</button>
      </div>
    </header>
  )
}

function RequireAuth({ children }: { children: ReactElement }) {
  const user = getUser()
  if (!user) return <Navigate to="/login" replace />
  return children
}

function RequireFirstTestDone({ children }: { children: ReactElement }) {
  const user = getUser()
  if (!user) return <Navigate to="/login" replace />
  if (!user.firstTestCompleted) return <Navigate to="/evaluation-choice" replace />
  return children
}

function BrainMascot() {
  const location = useLocation()
  if (location.pathname === '/') return null

  return (
    <aside className="brain-mascot" aria-hidden>
      <img src={DoctorResearching} alt="" className="brain-mascot-image" />
      <div className="brain-mascot-bubble">今天也来做一点脑力体操！</div>
    </aside>
  )
}

function FirstVisitModal({ onDismiss }: { onDismiss: () => void }) {
  return (
    <div className="first-visit-overlay">
      <div className="first-visit-card">
        <img src={DoctorResearching} alt="" className="first-visit-image" />
        <h2>欢迎来到脑力训练！</h2>
        <div className="first-visit-text">
          <div className="first-visit-item">
            <span className="first-visit-icon">🧠</span>
            <span>首次使用需要<b>下载手势识别模型</b>（约 40MB），请耐心等待加载完成</span>
          </div>
          <div className="first-visit-item">
            <span className="first-visit-icon">📷</span>
            <span>游戏需要<b>使用摄像头</b>来识别您的手势，浏览器会弹出权限请求，请点击"允许"</span>
          </div>
        </div>
        <button className="btn" style={{padding: '12px 48px', fontSize: 16, marginTop: 16}} onClick={onDismiss}>
          我知道了
        </button>
      </div>
    </div>
  )
}

function App(){
  const location = useLocation()
  const isCoverPage = location.pathname === '/'
  const isGamePage = location.pathname.startsWith('/games/')
  const showHeader = !isCoverPage && !isGamePage
  const showMascot = !isCoverPage && !isGamePage
  const [firstVisit, setFirstVisit] = useState(() => localStorage.getItem('first_visit_done') !== '1')

  return (
    <PresentationProvider>
      <>
        {showHeader && <Header />}
        <div className={isCoverPage ? 'container container-cover' : 'container'}>
          <Routes>
            <Route path="/" element={<GameCover />} />
            <Route path="/login" element={<Login/>} />
            <Route path="/register" element={<Registration/>} />
            <Route path="/role-select" element={<RequireAuth><RoleSelect/></RequireAuth>} />
            <Route path="/evaluation-choice" element={<RequireAuth><EvaluationChoice/></RequireAuth>} />
            <Route path="/onboarding" element={<RequireAuth><Onboarding/></RequireAuth>} />
            <Route path="/start" element={<RequireFirstTestDone><Start/></RequireFirstTestDone>} />
            <Route path="/difficulty-result" element={<RequireAuth><DifficultyResult/></RequireAuth>} />
            <Route path="/games/suan-shi" element={<RequireAuth><SuanShiHuiSuo/></RequireAuth>} />
            <Route path="/games/shu-xiang" element={<RequireFirstTestDone><ShuXiangZi/></RequireFirstTestDone>} />
            <Route path="/games/rps" element={<RequireFirstTestDone><RPS/></RequireFirstTestDone>} />
            <Route path="/reports" element={<RequireFirstTestDone><Reports/></RequireFirstTestDone>} />
            <Route path="/profile" element={<RequireAuth><Profile/></RequireAuth>} />
          </Routes>
        </div>
        {showMascot && <BrainMascot />}
        {firstVisit && (
          <FirstVisitModal onDismiss={() => {
            localStorage.setItem('first_visit_done', '1')
            setFirstVisit(false)
          }} />
        )}
      </>
    </PresentationProvider>
  )
}

function AppWithRouter() {
  return (
    <BrowserRouter>
      <App />
    </BrowserRouter>
  )
}

export default AppWithRouter
