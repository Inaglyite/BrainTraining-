import { useEffect, useRef, useState } from 'react'
import { startPreview, stopPreview, startDetection, stopDetection, stopCamera } from '../services/camera.ts'
import { isHandLandmarkerReady } from '../services/handLandmarker.ts'
import { usePresentation } from '../contexts/usePresentation'
import type { GestureSet } from '../types/api.ts'

export default function CameraPreview({ cornerMode = false, minimal = false, detectionMode = 'digits' }: { cornerMode?: boolean; minimal?: boolean; detectionMode?: GestureSet }){
  const isMinimal = cornerMode || minimal
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const [active, setActive] = useState(false)
  const [detecting, setDetecting] = useState(false)
  const [diff, setDiff] = useState<number | null>(null)
  const [lastGesture, setLastGesture] = useState<string | null>(null)
  const [lastSource, setLastSource] = useState<string | null>(null)
  const [lastConfidence, setLastConfidence] = useState<number | null>(null)
  const [handVisible, setHandVisible] = useState(false)
  const handSeenTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const { presentation } = usePresentation()

  useEffect(()=>{
    function onDetection(e: Event){
      const ev = e as CustomEvent<{diff:number, motionThreshold:number, gesture?: string, source?: string, confidence?: number | null}>
      setDiff(ev.detail?.diff ?? null)
    }
    function onGesture(e: Event){
      const ev = e as CustomEvent<{gesture?: string, source?: string, confidence?: number | null}>
      if (ev.detail?.gesture) setLastGesture(ev.detail.gesture)
      if (ev.detail?.source) setLastSource(ev.detail.source)
      if (typeof ev.detail?.confidence === 'number') setLastConfidence(ev.detail.confidence)
      setHandVisible(true)
      if (handSeenTimer.current) { clearTimeout(handSeenTimer.current) }
      handSeenTimer.current = setTimeout(() => setHandVisible(false), 1500)
    }
    window.addEventListener('camera_detection', onDetection as EventListener)
    window.addEventListener('camera_gesture', onGesture as EventListener)
    return ()=>{
      window.removeEventListener('camera_detection', onDetection as EventListener)
      window.removeEventListener('camera_gesture', onGesture as EventListener)
      stopDetection()
      stopPreview()
    }
  }, [])

  useEffect(()=>{
    // auto start in minimal mode
    if (isMinimal && videoRef.current) {
      startPreview(videoRef.current).then(ok => {
        setActive(ok)
        if (ok) {
          startDetection({ sampleRateMs: 200, motionThreshold: 30000, gestureSet: detectionMode })
          setDetecting(true)
        }
      })
    }

    return ()=>{
      if (isMinimal) {
        stopDetection()
        stopPreview()
      }
    }
  }, [detectionMode, isMinimal])

  async function handleStart(){
    if (!videoRef.current) return
    const ok = await startPreview(videoRef.current)
    setActive(ok)
  }
  function handleStop(){
    stopPreview()
    setActive(false)
    stopDetection()
    setDetecting(false)
    setDiff(null)
  }
  function handleStartDetect(){
    startDetection({ sampleRateMs: 200, motionThreshold: 30000, gestureSet: detectionMode })
    setDetecting(true)
  }
  function handleStopDetect(){
    stopDetection()
    setDetecting(false)
  }

  if (isMinimal) {
    return (
      <div className="video-wrap" style={{width: '100%', display: 'block', margin: 0}}>
        <video ref={videoRef} style={{width: '100%', height: 'auto', background:'#000', display:'block', borderRadius: 16}} playsInline muted autoPlay />
        <div className="video-indicator" style={{position: 'absolute', top: 8, left: 8, padding: '4px 10px', borderRadius: 999, background: 'rgba(0,0,0,0.6)', color: '#fff', border: 'none', display: 'flex', alignItems: 'center', gap: 6}}>
          <div className={`video-dot ${detecting? 'active' : 'inactive'}`}></div>
          <span style={{fontSize: 12, fontWeight: 600}}>
            {!isHandLandmarkerReady() ? '模型预加载中...' :
             active ? (detecting ? (handVisible ? '已检测到手' : '识别中...') : '已就绪') : '启动相机...'}
          </span>
        </div>
        {!presentation && lastGesture && (
          <div style={{position:'absolute', left: 8, bottom: 8, background:'rgba(0,0,0,0.65)', color:'#fff', padding:'6px 10px', borderRadius: 12, fontSize: 12}}>
            最近识别：{lastGesture}{lastSource ? ` (${lastSource})` : ''}{typeof lastConfidence === 'number' ? ` / ${lastConfidence.toFixed(2)}` : ''}
          </div>
        )}
      </div>
    )
  }

  return (
    <div>
      <div style={{display:'flex', gap:8, alignItems:'center'}}>
        <div className="video-wrap">
          <video ref={videoRef} style={{width:320, height:240, background:'#000', borderRadius:8}} playsInline muted autoPlay />
          <div className="video-indicator">
            <div className={`video-dot ${detecting? 'active' : 'inactive'}`}></div>
            <div style={{display:'flex', flexDirection:'column'}}>
              <div style={{fontWeight:700}}>{detecting? '检测中' : '未检测'}</div>
              {!presentation && <div className="meta">diff: {diff===null? '-' : diff}</div>}
            </div>
          </div>
        </div>

        {!presentation && (
          <div style={{display:'flex', flexDirection:'column', gap:8}}>
            {!active? <button className="btn" onClick={handleStart}>启用摄像头</button> : <button className="btn secondary" onClick={handleStop}>停止预览</button>}
            {!detecting? <button className="btn" onClick={handleStartDetect}>开始检测</button> : <button className="btn secondary" onClick={handleStopDetect}>停止检测</button>}
            <button className="btn secondary" onClick={()=>{ stopCamera(); setActive(false); setDetecting(false); setDiff(null) }}>关闭相机</button>
          </div>
        )}
      </div>

      {!presentation && (
        <div style={{marginTop: 16}}>
          <label className="meta">当前动作数值 (diff)</label>
          <div style={{
            marginTop: 8,
            padding: '12px 16px',
            borderRadius: 8,
            background: '#f8fafc',
            border: '1px solid var(--border)',
            fontSize: 20,
            fontWeight: 600,
            color: 'var(--accent)',
            display: 'inline-block',
            minWidth: 120,
            textAlign: 'center'
          }}>
            {diff === null ? '-' : diff}
          </div>
        </div>
      )}

      <p className="meta" style={{marginTop: 16}}>
        相机状态：{active? '已启用' : '未启用'}，检测：{detecting? '运行中' : '未运行'}
      </p>
    </div>
  )
}
