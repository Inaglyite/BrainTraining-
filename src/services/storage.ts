const USER_KEY = 'ys_user_v1'
const SESSIONS_KEY = 'ys_sessions_v1'
const TRAINING_TOTAL_SECONDS_KEY = 'ys_training_total_seconds_v1'

export interface User {
  userId: string
  birthday: string
  role?: 'student' | 'worker' | 'elder'
  firstTestCompleted: boolean
  createdAt: number
}
export interface Session {
  type: string
  payload?: unknown
  timestamp: number
}

export function saveUser(user: User){
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}
export function getUser(): User | null{
  const raw = localStorage.getItem(USER_KEY)
  return raw? JSON.parse(raw) as User : null
}

export function saveSession(session: Session){
  const arr = getSessions()
  arr.push(session)
  localStorage.setItem(SESSIONS_KEY, JSON.stringify(arr))
}
export function getSessions(): Session[]{
  const raw = localStorage.getItem(SESSIONS_KEY)
  return raw? JSON.parse(raw) as Session[] : []
}

export function clearAll(){
  localStorage.removeItem(USER_KEY)
  localStorage.removeItem(SESSIONS_KEY)
  localStorage.removeItem(TRAINING_TOTAL_SECONDS_KEY)
}

export function updateFirstTestCompleted(completed: boolean){
  const user = getUser()
  if (!user) return
  user.firstTestCompleted = completed
  saveUser(user)
}

export function getTrainingTotalSeconds(): number {
  const raw = localStorage.getItem(TRAINING_TOTAL_SECONDS_KEY)
  if (!raw) return 0
  const parsed = Number(raw)
  return Number.isFinite(parsed) && parsed >= 0 ? Math.floor(parsed) : 0
}

export function addTrainingDuration(seconds: number): number {
  const safeDelta = Number.isFinite(seconds) && seconds > 0 ? Math.floor(seconds) : 0
  const next = getTrainingTotalSeconds() + safeDelta
  localStorage.setItem(TRAINING_TOTAL_SECONDS_KEY, String(next))
  return next
}

