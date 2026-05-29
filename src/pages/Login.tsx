import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login } from '../services/authApi'
import { ApiError } from '../services/api'
import { saveUser } from '../services/storage'

export default function Login() {
  const navigate = useNavigate()
  const [userId, setUserId] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const profile = await login({ user_id: userId.trim(), password })
      saveUser({
        userId: profile.user_id,
        birthday: profile.birthday,
        role: profile.role,
        firstTestCompleted: profile.first_test_completed,
        createdAt: Date.now()
      })
      // 如果已完成首测，直接进入首页；否则进入评估页面
      if (profile.first_test_completed) {
        navigate('/start')
      } else {
        navigate('/evaluation-choice')
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '登录失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="card" style={{maxWidth: 420, margin: '60px auto', padding: '40px 30px', textAlign: 'center'}}>
      <h1 style={{fontSize: 28, marginBottom: 8}}>账号登录</h1>
      <p className="meta" style={{marginBottom: 28}}>登录后将自动判断是否需要首次测试</p>

      <form onSubmit={handleSubmit} style={{display:'flex', flexDirection:'column', gap:16}}>
        <input type="text" value={userId} onChange={e => setUserId(e.target.value)} placeholder="注册ID" required />
        <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="密码" required />
        {error && <div className="meta" style={{color:'#ef4444'}}>{error}</div>}
        <button type="submit" className="btn" disabled={loading}>{loading ? '登录中...' : '登录'}</button>
      </form>

      <p className="meta" style={{marginTop: 16}}>
        还没有账号？<Link to="/register" className="link-inline">去注册</Link>
      </p>
    </main>
  )
}

