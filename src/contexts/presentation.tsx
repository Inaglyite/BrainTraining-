import { useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import { PresentationContext } from './presentation-context'

export function PresentationProvider({ children }: { children: ReactNode }){
  const [presentation, setPresentation] = useState<boolean>(() => {
    try{
      const raw = localStorage.getItem('presentation_mode')
      return raw === '1'
    }catch{
      return false
    }
  })

  useEffect(()=>{
    const value = presentation ? '1' : '0'
    try{ localStorage.setItem('presentation_mode', value) }
    catch{ void value }
  }, [presentation])

  return (
    <PresentationContext.Provider value={{ presentation, setPresentation }}>
      {children}
    </PresentationContext.Provider>
  )
}
