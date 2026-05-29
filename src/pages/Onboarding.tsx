import { useNavigate } from 'react-router-dom'
import CameraPreview from '../components/CameraPreview.tsx'

export default function Onboarding() {
  const navigate = useNavigate()

  return (
    <main className="container" style={{maxWidth: 900}}>
      <div className="card" style={{padding: '40px 32px', textAlign: 'center'}}>
        <div style={{width: 72, height: 72, background: 'var(--accent-bg)', color: 'var(--accent)', borderRadius: 18, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 18px'}}>
          <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 14V10C21 8.89543 20.1046 8 19 8H5C3.89543 8 3 8.89543 3 10V14C3 15.1046 3.89543 16 5 16H19C20.1046 16 21 15.1046 21 14Z" />
            <path d="M7 8V6C7 4.89543 7.89543 4 9 4H15C16.1046 4 17 4.89543 17 6V8" />
            <path d="M12 16V20" />
            <path d="M8 20H16" />
          </svg>
        </div>
        <h1 style={{margin: 0, fontSize: 28}}>摄像头校准</h1>
        <p className="meta" style={{margin: '12px 0 28px'}}>请将手放入镜头范围内，系统将自动识别并进入训练流程。</p>

        <div style={{display: 'flex', justifyContent: 'center'}}>
          <div style={{width: '100%', maxWidth: 520}}>
            <CameraPreview />
          </div>
        </div>

        <div className="controls" style={{justifyContent: 'center', marginTop: 28}}>
          <button onClick={() => navigate('/start')} className="btn secondary">跳过并继续</button>
          <button onClick={() => navigate('/start')} className="btn">完成校准</button>
        </div>
      </div>
    </main>
  )
}
