import { useNavigate } from 'react-router-dom'
import { getUser, saveUser } from '../services/storage'

export default function RoleSelect() {
  const navigate = useNavigate()

  function handleSelect(role: 'student' | 'worker' | 'elder') {
    const user = getUser()
    if (user) {
      user.role = role
      saveUser(user)
      navigate('/evaluation-choice')
    }
  }

  return (
    <main className="container" style={{maxWidth: 800, textAlign: 'center', minHeight: '70vh', display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
      <h1 className="start-title" style={{fontSize: 32}}>请选择您的角色</h1>
      <p className="meta" style={{marginBottom: 40}}>不同的角色将为您提供更适合的训练计划</p>

      <div style={{display: 'flex', gap: 24, justifyContent: 'center', flexWrap: 'wrap'}}>
        <div className="card role-card" onClick={() => handleSelect('student')} style={{cursor: 'pointer', flex: '1 1 200px', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '32px 20px'}}>
          <div style={{fontSize: 48, marginBottom: 16}}>🎓</div>
          <h2 style={{margin: 0, fontSize: 20}}>学生党</h2>
          <p className="meta" style={{marginTop: 8}}>增强注意力与记忆力</p>
        </div>

        <div className="card role-card" onClick={() => handleSelect('worker')} style={{cursor: 'pointer', flex: '1 1 200px', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '32px 20px'}}>
          <div style={{fontSize: 48, marginBottom: 16}}>💼</div>
          <h2 style={{margin: 0, fontSize: 20}}>上班族</h2>
          <p className="meta" style={{marginTop: 8}}>缓解疲劳与活跃思维</p>
        </div>

        <div className="card role-card" onClick={() => handleSelect('elder')} style={{cursor: 'pointer', flex: '1 1 200px', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '32px 20px'}}>
          <div style={{fontSize: 48, marginBottom: 16}}>☕</div>
          <h2 style={{margin: 0, fontSize: 20}}>银发族</h2>
          <p className="meta" style={{marginTop: 8}}>保持大脑活力与反应</p>
        </div>
      </div>
    </main>
  )
}

