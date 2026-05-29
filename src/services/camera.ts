import { saveSession } from './storage.ts'
import { classifyLandmarks } from './gameApi.ts'
import type { GestureSet } from '../types/api.ts'
import { initHandLandmarker, getHandLandmarker, extractLandmarks } from './handLandmarker.ts'

type CameraGesture = string

let stream: MediaStream | null = null
let video: HTMLVideoElement | null = null
let running = false
let lastImageData: ImageData | null = null
let detectInterval: number | null = null
let inferInFlight = false
let latestLandmarks: number[] | null = null
let latestFrameDiff: number | null = null
let latestFrameMotionThreshold: number | null = null
let ctx: CanvasRenderingContext2D | null = null
let canvas: HTMLCanvasElement | null = null
let handSeenCount = 0
let frameCount = 0
let lastHandSeenLog = 0
let dimsLogged = false

export async function startPreview(videoEl: HTMLVideoElement) {
  try {
    if (!stream) {
      stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false })
    }
    video = videoEl
    video.autoplay = true
    video.muted = true
    video.playsInline = true
    video.srcObject = stream
    await new Promise<void>((resolve) => {
      if (video && video.readyState >= 1) {
        resolve()
        return
      }
      video?.addEventListener('loadedmetadata', () => resolve(), { once: true })
    })
    await video.play()
    console.log('[Camera] Video playing, dimensions:', video.videoWidth, 'x', video.videoHeight)
    await initHandLandmarker()
    return true
  } catch (err) {
    console.error('startPreview error', err)
    return false
  }
}

export function stopPreview() {
  if (video) {
    video.pause()
    video.srcObject = null
    video = null
  }
}

export async function stopCamera() {
  stopPreview()
  if (stream) {
    stream.getTracks().forEach(t => t.stop())
    stream = null
  }
  running = false
  inferInFlight = false
  latestLandmarks = null
  latestFrameDiff = null
  latestFrameMotionThreshold = null
  handSeenCount = 0
  frameCount = 0
  dimsLogged = false
  if (detectInterval) {
    window.clearInterval(detectInterval)
    detectInterval = null
  }
}

function dispatchGesture(g: CameraGesture, diff?: number, motionThreshold?: number, meta?: { source?: 'fallback' | 'backend'; rawLabel?: string; confidence?: number | null }){
  const detail = { gesture: g, diff, motionThreshold, ...meta }
  window.dispatchEvent(new CustomEvent('camera_gesture', { detail }))
  try{
    saveSession({ type: 'camera_gesture', payload: detail, timestamp: Date.now() })
  }catch{
    // fail silently
  }
}

function isRecognizedGesture(gesture: string, gestureSet: GestureSet) {
  if (gestureSet === 'rps') {
    return ['rock', 'paper', 'scissors'].includes(gesture)
  }
  return /^[1-9]$/.test(gesture)
}

export function startDetection(opts?: { sampleRateMs?: number, motionThreshold?: number, gestureSet?: GestureSet }){
  if (running) return
  const sampleRateMs = opts?.sampleRateMs ?? 200
  const motionThreshold = opts?.motionThreshold ?? 50_000
  const gestureSet = opts?.gestureSet ?? 'digits'

  if (!video) {
    console.warn('startDetection: no preview video attached')
    return
  }

  running = true

  canvas = document.createElement('canvas')
  canvas.width = 640
  canvas.height = 480
  ctx = canvas.getContext('2d', { willReadFrequently: true })
  lastImageData = null
  latestLandmarks = null
  latestFrameDiff = null
  latestFrameMotionThreshold = null
  dimsLogged = false

  const processLatestLandmarks = async () => {
    if (!running || inferInFlight || !latestLandmarks) return

    const landmarks = latestLandmarks
    const frameDiff = latestFrameDiff
    const frameMotionThreshold = latestFrameMotionThreshold
    latestLandmarks = null
    latestFrameDiff = null
    latestFrameMotionThreshold = null
    inferInFlight = true

    try {
      const inference = await classifyLandmarks(landmarks, gestureSet)
      const gesture = inference.gesture
      if (gesture && isRecognizedGesture(gesture, gestureSet)) {
        dispatchGesture(gesture, frameDiff ?? undefined, frameMotionThreshold ?? motionThreshold, {
          source: 'backend',
          rawLabel: inference.raw_label ?? inference.gesture,
          confidence: inference.confidence,
        })
      }
    } catch (e) {
      console.warn('gesture classify error', e)
    } finally {
      inferInFlight = false
      if (running && latestLandmarks) {
        void processLatestLandmarks()
      }
    }
  }

  detectInterval = window.setInterval(() => {
    if (!ctx || !video) return
    try {
      ctx.drawImage(video, 0, 0, canvas!.width, canvas!.height)

      const landmarker = getHandLandmarker()
      if (!landmarker) return

      if (!dimsLogged) {
        console.log('[Camera] Canvas:', canvas!.width, 'x', canvas!.height,
                    '| Video:', video.videoWidth, 'x', video.videoHeight,
                    '| readyState:', video.readyState)
        dimsLogged = true
      }

      const result = landmarker.detect(video)

      if (frameCount === 0) {
        console.log('[Camera] First detect() result keys:', Object.keys(result))
        console.log('[Camera] landmarks:', result.landmarks?.length ?? 0)
        console.log('[Camera] handedness:', result.handedness?.length ?? 0)
        console.log('[Camera] worldLandmarks:', result.worldLandmarks?.length ?? 0)
      }

      const { landmarks, handDetected } = extractLandmarks(result, performance.now())

      // Frame diff for UI
      const img = ctx.getImageData(0, 0, canvas!.width, canvas!.height)
      let measuredDiff: number | null = null
      if (lastImageData) {
        let diff = 0
        const len = img.data.length
        for (let i = 0; i < len; i += 4) {
          diff += Math.abs(img.data[i] - lastImageData.data[i])
            + Math.abs(img.data[i+1] - lastImageData.data[i+1])
            + Math.abs(img.data[i+2] - lastImageData.data[i+2])
        }
        measuredDiff = diff
        window.dispatchEvent(new CustomEvent('camera_detection', { detail: { diff, motionThreshold } }))
      }
      lastImageData = img

      frameCount++
      if (handDetected) {
        handSeenCount++
        if (Date.now() - lastHandSeenLog > 3000) {
          console.log(`[Camera] Hand detected (${handSeenCount}/${frameCount} frames). Sending landmarks to backend...`)
          lastHandSeenLog = Date.now()
        }
        latestLandmarks = landmarks
        latestFrameDiff = measuredDiff
        latestFrameMotionThreshold = motionThreshold
        void processLatestLandmarks()
      } else if (frameCount % 15 === 0) {
        console.log(`[Camera] No hand detected (${handSeenCount}/${frameCount} frames). Check lighting and hand position.`)
      }
    } catch (e) {
      console.warn('detection error', e)
    }
  }, sampleRateMs)
}

export function stopDetection(){
  running = false
  if (detectInterval) {
    window.clearInterval(detectInterval)
    detectInterval = null
  }
  lastImageData = null
  inferInFlight = false
  latestLandmarks = null
  latestFrameDiff = null
  latestFrameMotionThreshold = null
  handSeenCount = 0
  frameCount = 0
  dimsLogged = false
}
