import * as React from 'react'
import { PresentationContext } from './presentation-context'

export function usePresentation(){
  const ctx = React.useContext(PresentationContext)
  if (!ctx) throw new Error('usePresentation must be used inside PresentationProvider')
  return ctx
}
