import type { AIAnalysisResponse, AgentChatResponse, DailySummaryResponse, GameName, GestureDetectResponse, GestureSet, InteractionRecord, KnowledgeStateResponse, ModelConclusionRequest, ModelConclusionResponse, PeriodSummaryResponse, SessionActionResponse, SessionState, SummaryPeriod, UserAbilityResponse } from '../types/api'
import { apiRequest } from './api'

export function createSession(
  game: GameName,
  durationSeconds = 60,
  options?: { userId?: string; difficultyLevel?: number }
): Promise<SessionState> {
  return apiRequest<SessionState>(`/games/${game}/sessions`, {
    method: 'POST',
    body: JSON.stringify({
      duration_seconds: durationSeconds,
      user_id: options?.userId ?? 'anonymous',
      difficulty_level: options?.difficultyLevel ?? 1.0
    })
  })
}

export function getSession(game: GameName, sessionId: string): Promise<SessionState> {
  return apiRequest<SessionState>(`/games/${game}/sessions/${sessionId}`)
}

export function submitAction(game: GameName, sessionId: string, gesture: string): Promise<SessionActionResponse> {
  return apiRequest<SessionActionResponse>(`/games/${game}/sessions/${sessionId}/actions`, {
    method: 'POST',
    body: JSON.stringify({ gesture })
  })
}

export function getSessionInteractions(game: GameName, sessionId: string, limit = 200): Promise<InteractionRecord[]> {
  return apiRequest<InteractionRecord[]>(`/games/${game}/sessions/${sessionId}/interactions?limit=${limit}`)
}

export function detectGesture(imageBase64: string, gestureSet: GestureSet = 'digits'): Promise<GestureDetectResponse> {
  return apiRequest<GestureDetectResponse>(`/vision/gestures`, {
    method: 'POST',
    body: JSON.stringify({ image_base64: imageBase64, min_confidence: 0.3, gesture_set: gestureSet })
  })
}

export function classifyLandmarks(landmarks: number[], gestureSet: GestureSet = 'digits'): Promise<GestureDetectResponse> {
  return apiRequest<GestureDetectResponse>('/vision/classify', {
    method: 'POST',
    body: JSON.stringify({ landmarks, gesture_set: gestureSet })
  })
}

export function getDailySummary(userId: string, date?: string): Promise<DailySummaryResponse> {
  const query = date ? `?date=${encodeURIComponent(date)}` : ''
  return apiRequest<DailySummaryResponse>(`/games/users/${encodeURIComponent(userId)}/daily-summary${query}`)
}

export function getPeriodSummary(userId: string, period: SummaryPeriod, anchorDate?: string): Promise<PeriodSummaryResponse> {
  const query = new URLSearchParams({ period })
  if (anchorDate) query.set('anchor_date', anchorDate)
  return apiRequest<PeriodSummaryResponse>(`/games/users/${encodeURIComponent(userId)}/period-summary?${query.toString()}`)
}

export function generateModelConclusion(payload: ModelConclusionRequest): Promise<ModelConclusionResponse> {
  return apiRequest<ModelConclusionResponse>('/reports/model-conclusion', {
    method: 'POST',
    body: JSON.stringify(payload)
  })
}

export function getAIAnalysis(userId: string, period: SummaryPeriod, anchorDate?: string): Promise<AIAnalysisResponse> {
  return apiRequest<AIAnalysisResponse>('/reports/ai-analysis', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, period, anchor_date: anchorDate ?? null })
  })
}

export function getUserAbility(userId: string): Promise<UserAbilityResponse> {
  return apiRequest<UserAbilityResponse>(`/games/users/${encodeURIComponent(userId)}/ability`)
}

export function getKnowledgeState(userId: string): Promise<KnowledgeStateResponse[]> {
  return apiRequest<KnowledgeStateResponse[]>(`/games/users/${encodeURIComponent(userId)}/knowledge-state`)
}

export function sendAgentMessage(userId: string, message: string): Promise<AgentChatResponse> {
  return apiRequest<AgentChatResponse>('/agent/chat', {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, message })
  })
}
