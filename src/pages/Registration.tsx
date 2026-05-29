import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../services/authApi'
import { ApiError } from '../services/api'
import { saveUser } from '../services/storage'

export default function Registration() {
  const navigate = useNavigate()
  const [userId, setUserId] = useState('')
  const [password, setPassword] = useState('')
  const [birthday, setBirthday] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent){
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const profile = await register({
        user_id: userId.trim(),
        password,
        birthday,
        role: 'student',
      })
      saveUser({
        userId: profile.user_id,
        birthday: profile.birthday,
        role: undefined,
        firstTestCompleted: false,
        createdAt: Date.now(),
      })
      navigate('/role-select')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '注册失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="card" style={{maxWidth: 420, margin: '60px auto', padding: '40px 30px', textAlign: 'center'}}>
      <h1 style={{fontSize: 28, marginBottom: 8}}>创建账号</h1>
      <p className="meta" style={{marginBottom: 28}}>填写基本信息开始使用</p>

      <form onSubmit={handleSubmit} style={{display:'flex', flexDirection:'column', gap:14}}>
        <input type="text" value={userId} onChange={e => setUserId(e.target.value)} placeholder="注册ID" required />
        <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="设置密码(至少6位)" required minLength={6} />
        <input type="date" value={birthday} onChange={e => setBirthday(e.target.value)} required />

        {error && <div className="meta" style={{color:'#ef4444'}}>{error}</div>}
        <button type="submit" className="btn" disabled={loading}>{loading ? '注册中...' : '下一步'}</button>
      </form>

      <p className="meta" style={{marginTop: 16}}>
        已有账号？<Link to="/login" className="link-inline">去登录</Link>
      </p>
    </main>
  )
}
