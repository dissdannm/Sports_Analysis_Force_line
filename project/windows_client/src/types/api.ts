// windows_client/src/types/api.ts

export type MotionItem = {
  motion_id: string
  motion_name: string
  version: string
  description: string
}

export type MotionListResponse = {
  items: MotionItem[]
}

export type MotionDetailResponse = {
  motion_id: string
  motion_name: string
  version: string
  description: string
  landmarks_required: string[]
  enabled_metrics: string[]
  tags: string[]
  stable_frames: number
  voice_cooldown_ms: number
  min_hold_ms: number
}

export type LandmarkInput = {
  x: number
  y: number
  z?: number
  visibility?: number
}

export type AnalyzeFrameRequest = {
  motion_id: string
  session_id?: string | null
  timestamp_ms: number
  landmarks: Record<string, LandmarkInput>
}

export type AlertLevel = "mild" | "moderate" | "severe"

export type AlertResponse = {
  code: string
  level: AlertLevel
  message: string
  speak: boolean
  speak_text: string
  metric_id: string
  motion_id: string
}

export type AnalyzeFrameResponse = {
  motion_id: string
  session_id?: string | null
  timestamp_ms: number
  pose_detected: boolean
  metrics: Record<string, number>
  alerts: AlertResponse[]
}