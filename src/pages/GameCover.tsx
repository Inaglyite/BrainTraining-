import { useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getUser } from '../services/storage'
import GameCoverImage from '../assets/images/GameCover.png'
import DoctorCube from '../assets/images/Dr_Brain_Image/Doctor_Cube.png'

export default function GameCover() {
  const navigate = useNavigate()

  const handleContinue = useCallback(() => {
    const user = getUser()
    if (user) {
      if (user.firstTestCompleted) {
        navigate('/start')
      } else {
        navigate('/evaluation-choice')
      }
    } else {
      navigate('/login')
    }
  }, [navigate])

  useEffect(() => {
    const handleKeyPress = () => {
      handleContinue()
    }

    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [handleContinue])

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(circle at 86% 18%, rgba(255, 230, 109, 0.35), rgba(255, 230, 109, 0) 42%), radial-gradient(circle at 15% 88%, rgba(78, 205, 196, 0.2), rgba(78, 205, 196, 0) 40%), #FFF8EE',
      overflow: 'hidden',
      cursor: 'pointer'
    }} onClick={handleContinue}>
      <img
        src={GameCoverImage}
        alt="游戏封面"
        style={{
          maxWidth: '100%',
          maxHeight: '100%',
          objectFit: 'contain',
          opacity: 0,
          animation: 'coverFadeIn 900ms ease-out 120ms forwards'
        }}
      />

      <img
        src={DoctorCube}
        alt="博士方块"
        style={{
          position: 'absolute',
          right: '4vw',
          width: 'clamp(120px, 18vw, 280px)',
          maxHeight: '72vh',
          objectFit: 'contain',
          opacity: 0,
          animation: 'doctorRightIn 900ms ease-out 300ms forwards, doctorFloat 2.8s ease-in-out 1.2s infinite'
        }}
      />

      <p style={{
        position: 'absolute',
        bottom: '40px',
        color: '#2f220f',
        fontSize: '20px',
        fontWeight: '700',
        WebkitTextStroke: '3px #f7dba7',
        paintOrder: 'stroke fill',
        animation: 'pulse 2s ease-in-out infinite'
      }}>
        点击屏幕或按任意键继续
      </p>
      <style>{`
        @keyframes coverFadeIn {
          0% { opacity: 0; transform: scale(1.02); }
          100% { opacity: 1; transform: scale(1); }
        }

        @keyframes doctorLeftIn {
          0% { opacity: 0; transform: translateX(-22px) scale(0.96); }
          100% { opacity: 1; transform: translateX(0) scale(1); }
        }

        @keyframes doctorRightIn {
          0% { opacity: 0; transform: translateX(22px) scale(0.96); }
          100% { opacity: 1; transform: translateX(0) scale(1); }
        }

        @keyframes doctorFloat {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }

        @keyframes pulse {
          0%, 100% { opacity: 0.7; }
          50% { opacity: 1; }
        }

        @media (max-width: 900px) {
          img[alt="博士方块"] {
            width: clamp(96px, 28vw, 160px) !important;
            top: auto;
            bottom: 110px;
            max-height: 40vh;
            right: 1vw !important;
          }
        }
      `}</style>
    </div>
  )
}
