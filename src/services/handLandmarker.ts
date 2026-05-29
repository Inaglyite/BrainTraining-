import { HandLandmarker, FilesetResolver } from '@mediapipe/tasks-vision'

let handLandmarker: HandLandmarker | null = null
let initPromise: Promise<void> | null = null
let mode: 'GPU' | 'CPU' = 'GPU'

export function getHandLandmarkerMode(): string {
  return mode
}

export function isHandLandmarkerReady(): boolean {
  return handLandmarker !== null
}

export function preloadHandLandmarker(): void {
  if (!handLandmarker && !initPromise) {
    console.log('[HandLandmarker] Preloading started...')
    initPromise = initHandLandmarkerInternal()
  }
}

async function initHandLandmarkerInternal(): Promise<void> {
  console.log('[HandLandmarker] Loading WASM from /wasm...')
  const vision = await FilesetResolver.forVisionTasks('/wasm')
  console.log('[HandLandmarker] WASM loaded, creating landmarker...')
  const tryCreate = async (delegate: 'GPU' | 'CPU') => {
    return HandLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: '/models/hand_landmarker.task',
        delegate,
      },
      numHands: 1,
      minHandDetectionConfidence: 0.4,
      minTrackingConfidence: 0.4,
      minHandPresenceConfidence: 0.3,
      runningMode: 'IMAGE',
    })
  }
  try {
    handLandmarker = await tryCreate('GPU')
    mode = 'GPU'
    console.log('[HandLandmarker] Initialized with GPU delegate (IMAGE mode)')
  } catch (e) {
    console.warn('[HandLandmarker] GPU delegate failed, falling back to CPU:', e)
    try {
      handLandmarker = await tryCreate('CPU')
      mode = 'CPU'
      console.log('[HandLandmarker] Initialized with CPU delegate (IMAGE mode)')
    } catch (e2) {
      console.error('[HandLandmarker] CPU delegate also failed:', e2)
      throw e2
    }
  }
}

export async function initHandLandmarker(): Promise<void> {
  if (handLandmarker) return
  if (!initPromise) {
    initPromise = initHandLandmarkerInternal()
  }
  await initPromise
}

export function getHandLandmarker(): HandLandmarker | null {
  return handLandmarker
}

export function closeHandLandmarker(): void {
  if (handLandmarker) {
    handLandmarker.close()
    handLandmarker = null
    initPromise = null
  }
}

export interface HandLandmarks {
  landmarks: number[]  // 63 floats: [x0,y0,z0, x1,y1,z1, ..., x20,y20,z20]
  handDetected: boolean
}

export function extractLandmarks(result: any, _timestamp: number): HandLandmarks {
  const handLandmarks = result?.landmarks || result?.handLandmarks
  if (!handLandmarks?.length) {
    return { landmarks: [], handDetected: false }
  }

  const lm = handLandmarks[0]
  const flat: number[] = []
  for (const p of lm) {
    flat.push(p.x, p.y, p.z)
  }

  return { landmarks: flat, handDetected: true }
}
