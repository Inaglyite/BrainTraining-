import { createContext } from 'react'

export type PresentationContextValue = {
  presentation: boolean
  setPresentation: (v: boolean) => void
}

export const PresentationContext = createContext<PresentationContextValue | undefined>(undefined)

