import { getUser, clearAll } from '../services/storage.ts'
import { useNavigate } from 'react-router-dom'

export default function Profile(){
  const user = getUser()
  const navigate = useNavigate()

  return (
    <main className="container" style={{maxWidth: 600, margin: '40px auto'}}>
      <div className="card" style={{padding: '40px 30px'}}>
        <div style={{textAlign: 'center', marginBottom: 32}}>
          <h1 className="start-title" style={{fontSize: 28, marginBottom: 8}}>个人中心</h1>
          <p className="meta">管理您的信息和设置</p>
        </div>

        <div style={{padding: 24, background: '#f8fafc', borderRadius: 16, border: '1px solid var(--border)'}}>
          <div style={{display:'flex', alignItems:'center', gap: 20, marginBottom: 24}}>
            <div style={{width: 72, height: 72, borderRadius: '50%', background: 'var(--accent-bg)', color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 28, fontWeight: 'bold'}}>
              {user?.userId?.[0]?.toUpperCase() || 'U'}
            </div>
            <div>
              <h2 style={{margin: 0, fontSize: 22, color: 'var(--text-h)'}}>{user?.userId || '未注册'}</h2>
              <p className="meta" style={{margin: '4px 0 0 0'}}>生日: {user?.birthday || '-'}</p>
              {user?.role && (
                <div style={{marginTop: 8, display: 'inline-block', padding: '4px 10px', background: 'rgba(139, 92, 246, 0.1)', color: '#8b5cf6', borderRadius: 999, fontSize: 13, fontWeight: 600}}>
                  角色: {user.role === 'student' ? '学生党' : user.role === 'worker' ? '上班族' : '银发族'}
                </div>
              )}
            </div>
          </div>

          <div className="controls" style={{display:'flex', flexDirection:'column', gap:12}}>
            <button className="btn" style={{justifyContent:'flex-start', padding: '14px 20px', background: 'white', color: 'var(--text-h)', border: '1px solid var(--border)', boxShadow: '0 2px 8px rgba(0,0,0,0.02)'}} onClick={()=>alert('修改信息功能开发中...')}>修改个人信息</button>
            <button className="btn" style={{justifyContent:'flex-start', padding: '14px 20px', background: 'white', color: 'var(--text-h)', border: '1px solid var(--border)', boxShadow: '0 2px 8px rgba(0,0,0,0.02)'}} onClick={()=>alert('修改密码功能开发中...')}>修改密码</button>
          </div>
        </div>

        <div className="controls" style={{marginTop: 32, display: 'flex', flexDirection: 'column', gap: 12}}>
          <button onClick={()=>navigate('/onboarding')} className="btn secondary" style={{padding: '14px'}}>重新校准摄像头</button>
          <button onClick={()=>{ clearAll(); navigate('/')}} className="btn" style={{background:'#ef4444', padding: '14px', boxShadow: '0 4px 12px rgba(239, 68, 68, 0.2)'}}>退出登录并清除数据</button>
        </div>
      </div>
    </main>
  )
}
