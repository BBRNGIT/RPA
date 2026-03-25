/**
 * TypeScript types for RPA Core API.
 * Mirrors the Pydantic models from the backend.
 */

// ============================================================================
// ENUMS
// ============================================================================

export type UserRole = 'superadmin' | 'admin' | 'user' | 'guest';

export type ProficiencyLevel = 'new' | 'learning' | 'familiar' | 'proficient' | 'mastered';

export type ExerciseType = 'flashcard' | 'multiple_choice' | 'fill_blank' | 'typing' | 'error_correction';

export type DomainType = 'english' | 'python' | 'general';

// ============================================================================
// API RESPONSE
// ============================================================================

export interface APIResponse<T = unknown> {
  success: boolean;
  message: string;
  data?: T;
  errors?: string[];
  timestamp: string;
}

// ============================================================================
// USER MODELS
// ============================================================================

export interface UserPreferences {
  theme: 'light' | 'dark' | 'auto';
  difficulty: 'easy' | 'medium' | 'hard' | 'adaptive';
  daily_goal: number;
  notifications: boolean;
  sound_effects: boolean;
  editor: string;
  pager: string;
  font_size: number;
  high_contrast: boolean;
  reduced_motion: boolean;
}

export interface User {
  user_id: string;
  email: string;
  username: string;
  role: UserRole;
  preferences: UserPreferences;
  created_at: string;
  last_login?: string;
  is_active: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  role?: UserRole;
}

// ============================================================================
// LEARNING MODELS
// ============================================================================

export interface LearningSession {
  session_id: string;
  user_id: string;
  domain: DomainType;
  exercise_type: ExerciseType;
  current_item: number;
  total_items: number;
  correct_count: number;
  incorrect_count: number;
  accuracy: number;
  started_at: string;
  last_activity: string;
  is_active: boolean;
}

export interface LearningProgress {
  user_id: string;
  vocabulary: {
    total: number;
    mastered: number;
    learning: number;
    new: number;
  };
  grammar: {
    total: number;
    mastered: number;
  };
  reading: {
    articles_read: number;
    total_time: number;
  };
  writing: {
    essays_written: number;
    average_score: number;
  };
  streaks: {
    current: number;
    longest: number;
  };
  total_time_spent: number;
  last_session?: string;
  achievements: string[];
}

// ============================================================================
// VOCABULARY MODELS
// ============================================================================

export interface VocabularyItem {
  word_id: string;
  word: string;
  definition: string;
  part_of_speech: string;
  examples: string[];
  synonyms: string[];
  antonyms: string[];
  difficulty: number;
  proficiency: ProficiencyLevel;
  next_review?: string;
}

export interface VocabularyFlashcard {
  word_id: string;
  front: string;
  back: string;
  examples: string[];
  part_of_speech: string;
  difficulty: number;
  hint?: string;
}

export interface VocabularyMultipleChoice {
  word_id: string;
  question: string;
  options: string[];
  correct_index: number;
  difficulty: number;
}

export interface VocabularyReviewRequest {
  word_id: string;
  quality: number; // 0-5
  response: string;
  time_spent_seconds: number;
}

export interface VocabularyReviewResponse {
  word_id: string;
  correct: boolean;
  quality: number;
  feedback: string;
  new_proficiency: ProficiencyLevel;
  next_review: string;
  interval: number;
}

// ============================================================================
// GRAMMAR MODELS
// ============================================================================

export interface GrammarRule {
  rule_id: string;
  name: string;
  category: string;
  description: string;
  correct_examples: string[];
  incorrect_examples: string[];
  explanation: string;
  difficulty: number;
}

export interface GrammarExerciseRequest {
  rule_id?: string;
  category?: string;
  difficulty?: number;
  exercise_type: ExerciseType;
}

export interface GrammarExercise {
  exercise_id: string;
  rule_id: string;
  type: ExerciseType;
  question: string;
  options?: string[];
  correct_answer: string;
  explanation: string;
  difficulty: number;
}

export interface GrammarCheckRequest {
  text: string;
}

export interface GrammarCheckResponse {
  text: string;
  errors: Array<{
    position: number;
    message: string;
    suggestion: string;
  }>;
  suggestions: string[];
  score: number;
}

// ============================================================================
// READING/WRITING MODELS
// ============================================================================

export interface ReadingContent {
  content_id: string;
  title: string;
  text: string;
  level: number;
  word_count: number;
  estimated_time: number;
  domain: DomainType;
  tags: string[];
}

export interface WritingSubmission {
  submission_id: string;
  user_id: string;
  topic: string;
  text: string;
  word_count: number;
  submitted_at: string;
}

export interface WritingAssessment {
  submission_id: string;
  overall_score: number;
  grammar_score: number;
  vocabulary_score: number;
  coherence_score: number;
  structure_score: number;
  content_score: number;
  strengths: string[];
  weaknesses: string[];
  suggestions: string[];
}

// ============================================================================
// SYSTEM MODELS
// ============================================================================

export interface SystemStatus {
  status: string;
  version: string;
  stm_patterns: number;
  ltm_patterns: number;
  total_episodes: number;
  total_users: number;
  active_users: number;
  domains: string[];
}

export interface DashboardData {
  user: User;
  progress: LearningProgress;
  due_vocabulary: number;
  due_grammar: number;
  recent_sessions: Array<{
    session_id: string;
    domain: string;
    items_reviewed: number;
    accuracy: number;
    completed_at: string;
  }>;
  recommended_next: string[];
  today_items: number;
  today_time: number;
}

// ============================================================================
// ADMIN MODELS
// ============================================================================

export interface AdminUserUpdate {
  role?: UserRole;
  is_active?: boolean;
  preferences?: Partial<UserPreferences>;
}

export interface AdminReport {
  report_type: string;
  generated_at: string;
  data: {
    total_users: number;
    total_sessions: number;
    vocabulary_stats: Record<string, unknown>;
  };
}

// ============================================================================
// DESIGN TOKENS
// ============================================================================

export interface DesignTokens {
  colors: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
    text_muted: string;
    success: string;
    warning: string;
    error: string;
    info: string;
  };
  typography: {
    font_family: string;
    font_mono: string;
    sizes: {
      xs: string;
      sm: string;
      base: string;
      lg: string;
      xl: string;
      '2xl': string;
      '3xl': string;
    };
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    '2xl': string;
  };
  radius: {
    sm: string;
    md: string;
    lg: string;
    full: string;
  };
  shadows: {
    sm: string;
    md: string;
    lg: string;
  };
}
