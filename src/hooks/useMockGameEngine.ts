import { useEffect, useState } from 'react'

type Gesture = '1'|'2'|'3'|'4'|'5'|'6'|'7'|'8'|'9'
type CameraGestureDetail = { gesture?: string } | string

export default function useMockGameEngine(){
  const [gesture, setGesture] = useState<Gesture>('1')

  useEffect(()=>{
    function onKey(e: KeyboardEvent){
      if (e.key>='1' && e.key<='9') setGesture(e.key as Gesture)
    }
    function onCamera(e: Event){
      const ev = e as CustomEvent<CameraGestureDetail>
      const detail = ev.detail
      let g: string | undefined
      if (typeof detail === 'string') g = detail
      else if (detail && typeof detail === 'object') g = detail.gesture
      if (!g) return
      // only accept digit gestures from the camera/model
      if (g === '1' || g === '2' || g === '3' || g === '4' || g === '5' || g === '6' || g === '7' || g === '8' || g === '9'){
        setGesture(g as Gesture)
      }
    }

    window.addEventListener('keydown', onKey)
    window.addEventListener('camera_gesture', onCamera as EventListener)
    return () => {
      window.removeEventListener('keydown', onKey)
      window.removeEventListener('camera_gesture', onCamera as EventListener)
    }
  }, [])

  function triggerGesture(g: Gesture){ setGesture(g) }

  return { gesture, triggerGesture }
}
