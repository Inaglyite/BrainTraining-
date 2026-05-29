export type Gesture = '1'|'2'|'3'|'4'|'5'|'6'|'7'|'8'|'9'

export interface Player {
  nickname: string
  createdAt: number
}

export interface GameSession {
  id: string
  game: string
  score: number
  timestamp: number
}

