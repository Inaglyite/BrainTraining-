import { useNavigate, useLocation, Navigate } from 'react-router-dom'
import { useState } from 'react'
import DoctorCelebrate from '../assets/images/Dr_Brain_Image/Doctor_celebrate.png'
import DoctorResearching from '../assets/images/Dr_Brain_Image/Doctor_researching.png'
import type { DifficultyRecommendation } from '../types/api'

export default function DifficultyResult() {
  const navigate = useNavigate()
  const location = useLocation()
  const [isLoading, setIsLoading] = useState(false)

  // 从location.state获取难度调整结果
  const state = location.state as {
    accuracy: number
    nBackLevel: number
    gameName: string
    gameDuration?: number // 游戏时长（秒）
    totalTrainingSeconds?: number
    todayRemainingRounds?: number | null
    recommendation?: DifficultyRecommendation | null
  } | null

  if (!state) {
    return <Navigate to="/start" replace />
  }

  const { accuracy, nBackLevel, gameName, gameDuration, totalTrainingSeconds, todayRemainingRounds, recommendation } = state
  const safeGameDuration = gameDuration ?? 0
  const safeTotalTrainingSeconds = totalTrainingSeconds ?? 0
  const safeAccuracy = Math.min(1, Math.max(0, Number.isFinite(accuracy) ? accuracy : 0))
  const levelWillIncrease = safeAccuracy > 0.85
  const doctorImage = levelWillIncrease ? DoctorCelebrate : DoctorResearching
  const doctorAlt = levelWillIncrease ? '博士庆祝' : '博士研究中'
  
  const { message, icon, color } = safeAccuracy < 0.6
    ? {
        message: `正确率 ${(safeAccuracy * 100).toFixed(0)}% - 偏低`,
        icon: '📉',
        color: '#ef4444',
      }
    : safeAccuracy > 0.85
      ? {
          message: `正确率 ${(safeAccuracy * 100).toFixed(0)}% - 优秀`,
          icon: '📈',
          color: '#10b981',
        }
      : {
          message: `正确率 ${(safeAccuracy * 100).toFixed(0)}% - 稳定`,
          icon: '➡️',
          color: '#c67a1d',
        }

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${minutes}:${String(secs).padStart(2, '0')}`
  }

  async function handleContinue() {
    setIsLoading(true)
    // 根据游戏类型导航到对应游戏
    const gameRoutes: Record<string, string> = {
      '算式回溯': '/games/suan-shi',
      '数箱子': '/games/shu-xiang',
      '石头剪刀布': '/games/rps',
    }
    const route = gameRoutes[gameName] || '/start'
    setTimeout(() => {
      navigate(route)
    }, 500)
  }

  return (
    <main style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div className="card" style={{
        maxWidth: 500,
        textAlign: 'center',
        padding: '60px 40px'
      }}>
        <style>{`
          @keyframes doctorFadeIn {
            0% { opacity: 0; transform: translateY(8px) scale(0.98); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
          }
        `}</style>

        <div style={{ fontSize: 72, marginBottom: 24 }}>
          {icon}
        </div>

        <h1 style={{
          fontSize: 32,
          marginBottom: 16,
          color: 'var(--text-h)'
        }}>
          本局结束
        </h1>

        <img
          src={doctorImage}
          alt={doctorAlt}
          style={{
            width: '100%',
            maxWidth: 280,
            margin: '0 auto 24px',
            display: 'block',
            objectFit: 'contain',
            animation: 'doctorFadeIn 480ms ease-out both'
          }}
        />

        <div className="info-card" style={{
          marginBottom: 32,
          background: `${color}15`,
          borderColor: color
        }}>
          <div className="info-card-label" style={{ fontSize: 14 }}>
            {gameName} - 正确率
          </div>
          <div className="info-card-value" style={{
            fontSize: 28,
            color: color,
            fontWeight: 700
          }}>
            {(safeAccuracy * 100).toFixed(0)}%
          </div>
          <div className="meta" style={{ marginTop: 8, color: color }}>
            {message}
          </div>
        </div>

        <div className="info-card" style={{ marginBottom: 32 }}>
          <div className="info-card-label">本局数据</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 12 }}>
            <div>
              <div className="meta" style={{ marginBottom: 4 }}>正确率</div>
              <div className="info-card-value" style={{ fontSize: 24, color }}>{(safeAccuracy * 100).toFixed(0)}%</div>
            </div>
            <div>
              <div className="meta" style={{ marginBottom: 4 }}>用时</div>
              <div className="info-card-value" style={{ fontSize: 24 }}>{formatDuration(safeGameDuration)}</div>
            </div>
          </div>
        </div>

        <div className="info-card" style={{ marginBottom: 32 }}>
          <div className="info-card-label">累计训练时长</div>
          <div className="info-card-value" style={{ fontSize: 28 }}>
            {formatDuration(safeTotalTrainingSeconds)}
          </div>
        </div>

        <div className="info-card" style={{ marginBottom: 32 }}>
          <div className="info-card-label">数箱子今日剩余局数</div>
          <div className="info-card-value" style={{ fontSize: 28 }}>
            {typeof todayRemainingRounds === 'number' ? todayRemainingRounds : '-'}
          </div>
        </div>

        <div className="info-card" style={{ marginBottom: 32 }}>
          <div className="info-card-label">下一局难度</div>
          <div className="info-card-value" style={{ fontSize: 28 }}>
            {recommendation ? recommendation.recommended_difficulty.toFixed(1) : `${nBackLevel}-回溯`}
          </div>
          <div className="meta" style={{ marginTop: 8 }}>
            {recommendation?.explanation_cn ?? (
              <>
                {safeAccuracy < 0.6 && '难度已降低，希望继续加油！'}
                {safeAccuracy > 0.85 && '难度已提高，继续挑战自己！'}
                {safeAccuracy >= 0.6 && safeAccuracy <= 0.85 && '难度保持不变，继续稳定发挥！'}
              </>
            )}
          </div>
          {recommendation && (
            <div className="meta" style={{ marginTop: 6 }}>
              预测正确率 {(recommendation.predicted_p_correct * 100).toFixed(0)}%，置信度 {(recommendation.confidence * 100).toFixed(0)}%
            </div>
          )}
        </div>

        <button 
          className="btn"
          onClick={handleContinue}
          disabled={isLoading}
          style={{
            width: '100%',
            padding: '16px 24px',
            fontSize: 16,
            fontWeight: 600
          }}
        >
          {isLoading ? '加载中...' : '继续锻炼'}
        </button>

        <button 
          className="btn secondary"
          onClick={() => navigate('/start')}
          style={{
            width: '100%',
            marginTop: 12,
            padding: '16px 24px',
            fontSize: 16
          }}
        >
          结束锻炼
        </button>
      </div>
    </main>
  )
}


