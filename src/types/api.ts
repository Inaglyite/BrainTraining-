export type GestureName = string
export type GameName = 'shu-xiang' | 'suan-shi' | 'rps'
export type GestureSet = 'digits' | 'rps'

export interface GestureDetectResponse {
  gesture: GestureName
  raw_label: string | null
  confidence: number | null
  hand_detected: boolean
  threshold: number
}

export interface SessionState {
  session_id: string
  game: GameName
  score: number
  remaining_seconds: number
  elapsed_seconds: number
  status: 'active' | 'completed'
  user_id: string
  difficulty_level: number
  attempt_index: number
  consecutive_errors: number
  current_question: string | null
  n_back_level: number | null
  suanshi_total_questions: number | null
  suanshi_answered_questions: number | null
  suanshi_target_answer: number | null
  suanshi_can_answer: boolean | null
  suanshi_recent_answers: number[] | null
  box_count: number | null
  rps_instruction: 'win' | 'lose' | 'draw' | null
  rps_cpu_action: 'rock' | 'paper' | 'scissors' | null
  answer_time_limit_ms: number | null
  answer_remaining_ms: number | null
  difficulty_recommendation: DifficultyRecommendation | null
}

export interface DifficultyRecommendation {
  user_id: string
  game_type: '算式回溯' | '数箱子' | '指令石头剪刀布'
  current_difficulty: number
  recommended_difficulty: number
  action: 'increase' | 'decrease' | 'keep'
  target_band: [number, number]
  predicted_p_correct: number
  confidence: number
  reason_codes: Array<'theta_low' | 'theta_high' | 'in_band' | 'consecutive_errors' | 'slow_response'>
  explanation_cn: string
}

export interface SessionActionResponse {
  state: SessionState
  used_gesture: GestureName | null
  correct: boolean | null
  response_time: number | null
  inference: GestureDetectResponse | null
}

export interface InteractionRecord {
  id: number
  session_id: string
  user_id: string
  game_type: string
  difficulty_level: number
  attempt_index: number
  correct: boolean
  response_time: number
  consecutive_errors: number
  total_attempted: number
  skill_opportunities: number
  time_since_last_same_game: number | null
  help_used: boolean | null
  skip_used: boolean | null
  gesture: string | null
  created_at: number
}

export interface DailySessionItem {
  session_id: string
  game_type: GameName
  started_at: number
  duration_seconds: number
  score: number
  accuracy: number | null
  status: string
}

export interface DailySummaryResponse {
  user_id: string
  date: string
  total_duration_seconds: number
  total_sessions: number
  shu_xiang_sessions: number
  suan_shi_sessions: number
  rps_sessions: number
  shu_xiang_remaining_rounds: number
  sessions: DailySessionItem[]
}

export type SummaryPeriod = 'daily' | 'monthly' | 'quarterly'

export interface PeriodSummaryResponse {
  user_id: string
  period: SummaryPeriod
  anchor_date: string
  period_start: string
  period_end: string
  total_duration_seconds: number
  total_sessions: number
  shu_xiang_sessions: number
  suan_shi_sessions: number
  rps_sessions: number
  average_accuracy: number | null
  sessions: DailySessionItem[]
  report_text: string
}

export interface ModelMetricInput {
  accuracy: number | null
  auc: number | null
  brier: number | null
}

export interface ModelConclusionRequest {
  dataset_name: string
  train_size: number
  test_size: number
  metrics: Record<'IRT(1PL)' | 'DKT-Light' | 'LSTM-DKT' | 'RF-Seq' | 'XGBoost-Seq', ModelMetricInput>
  xgboost_aux?: {
    user_risk_segments?: {
      high_risk_ratio: number | null
      medium_risk_ratio: number | null
      low_risk_ratio: number | null
    }
    top_feature_importance?: Array<[string, number]>
  }
  target_flow_band: [number, number]
}

export interface ModelConclusionResponse {
  section_title: '第6节 模型性能与结论'
  content: string
}

export interface AIAnalysisRequest {
  user_id: string
  period: SummaryPeriod
  anchor_date?: string | null
}

export interface AIAnalysisResponse {
  user_id: string
  period: string
  analysis_text: string
  model_used: string
}

export interface GameAbility {
  xgb_p_correct: number | null
  xgb_confidence: number | null
  irt_theta: number | null
}

export interface UserAbilityResponse {
  user_id: string
  abilities: Record<string, GameAbility>
  model_status: Record<string, boolean>
}

export interface KnowledgeStateResponse {
  user_id: string
  game: string
  predicted_p_correct: number
  confidence: number
  recommendation: string
}

export interface AgentChatRequest {
  user_id: string
  message: string
}

export interface AgentChatResponse {
  user_id: string
  reply: string
  model_used: string
}
