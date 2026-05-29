import { Link } from 'react-router-dom'

export default function Start() {
  return (
    <main className="container" style={{maxWidth: 1000}}>
      <div style={{textAlign: 'center', marginBottom: 40}}>
        <h1 className="start-title">开启脑锻炼之旅！</h1>
        <p className="start-subtitle">每天坚持几分钟，提升专注力与反应速度</p>
      </div>

      <div style={{display: 'flex', gap: 20, marginTop: 12, flexWrap: 'wrap'}}>
        <Link to="/games/suan-shi" className="game-tile" style={{flex: '1 1 300px', textDecoration: 'none', color: 'inherit'}} aria-label="算式回溯">
          <div className="tile-icon" aria-hidden>
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
              <rect x="3" y="3" width="18" height="18" rx="3" stroke="currentColor" strokeWidth="1.5" fill="none" />
              <path d="M7 7h10M7 11h10M7 15h10" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <div>
            <h2>算式回溯</h2>
            <p className="meta">训练工作记忆与计算回溯能力</p>
          </div>
        </Link>

        <Link to="/games/shu-xiang" className="game-tile" style={{flex: '1 1 300px', textDecoration: 'none', color: 'inherit'}} aria-label="数箱子">
          <div className="tile-icon" aria-hidden>
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
              <path d="M3 7.5L12 3l9 4.5v9L12 21 3 16.5v-9z" stroke="currentColor" strokeWidth="1.5" fill="none" />
              <path d="M12 3v18" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
            </svg>
          </div>
          <div>
            <h2>数箱子</h2>
            <p className="meta">注意力、手眼协调与计数训练</p>
          </div>
        </Link>

        <Link to="/games/rps" className="game-tile" style={{flex: '1 1 300px', textDecoration: 'none', color: 'inherit'}} aria-label="石头剪刀布">
          <div className="tile-icon" aria-hidden>
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden>
              <path d="M12 2C7.58 2 4 5.58 4 10c0 5.25 6.7 11.06 7.2 11.5.28.25.72.25 1 0C13.3 21.06 20 15.25 20 10c0-4.42-3.58-8-8-8z" stroke="currentColor" strokeWidth="1.4" fill="none" />
              <path d="M10 9l4 0" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            </svg>
          </div>
          <div>
            <h2>石头剪刀布</h2>
            <p className="meta">快速反应与决策能力挑战</p>
          </div>
        </Link>
      </div>

      <div style={{display: 'flex', gap: 20, marginTop: 40, flexWrap: 'wrap'}}>
        <Link to="/reports" className="game-tile" style={{flex: '1 1 200px', textDecoration: 'none', color: 'inherit'}}>
          <div className="tile-icon" style={{background: '#f3c27b', color: '#5b3d19'}} aria-hidden>
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M4 19V5C4 4.44772 4.44772 4 5 4H19C19.5523 4 20 4.44772 20 5V19C20 19.5523 19.5523 20 19 20H5C4.44772 20 4 19.5523 4 19Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M8 16V12M12 16V8M16 16V10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <h2 style={{fontSize: 18}}>锻炼报告</h2>
            <p className="meta" style={{fontSize: 14}}>查看您的训练历史与趋势</p>
          </div>
        </Link>

        <Link to="/profile" className="game-tile" style={{flex: '1 1 200px', textDecoration: 'none', color: 'inherit'}}>
          <div className="tile-icon" style={{background: '#efb36a', color: '#5b3d19'}} aria-hidden>
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M20 21C20 18.2386 16.4183 16 12 16C7.58172 16 4 18.2386 4 21" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div>
            <h2 style={{fontSize: 18}}>个人中心</h2>
            <p className="meta" style={{fontSize: 14}}>管理账号与系统设置</p>
          </div>
        </Link>
      </div>
    </main>
  )
}
