// ══════════════════════════════════════════════════════════════
// frontend/src/types/ai.ts
// ══════════════════════════════════════════════════════════════
export interface PossibleCondition {
  condition: string
  confidence: number
  description: string
}
 
export interface SymptomCheckResult {
  symptoms_submitted: string
  analysis: {
    possible_conditions: PossibleCondition[]
    urgency_level: 'low' | 'medium' | 'high' | 'emergency'
    urgency_reason: string
    recommended_specialist: string
    recommended_actions: string[]
    red_flags: string[]
    disclaimer: string
  }
  response_time_ms: number
}
