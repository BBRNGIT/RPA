/**
 * RPA Core API Client
 * 
 * Connects to the FastAPI backend running on port 8000.
 * Uses the gateway with XTransformPort for routing.
 */

import type {
  User,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  DashboardData,
  LearningProgress,
  VocabularyItem,
  VocabularyFlashcard,
  VocabularyMultipleChoice,
  VocabularyReviewRequest,
  VocabularyReviewResponse,
  GrammarExerciseRequest,
  GrammarExercise,
  GrammarCheckRequest,
  GrammarCheckResponse,
  AdminUserUpdate,
  DesignTokens,
  APIResponse,
} from './types';

// API base path with port transform for gateway
const API_BASE = '/api';
const API_PORT = 8000;

/**
 * Build URL with XTransformPort parameter
 */
function buildUrl(endpoint: string, params?: Record<string, string | number | boolean>): string {
  const url = new URL(`${API_BASE}${endpoint}`, window.location.origin);
  url.searchParams.set('XTransformPort', String(API_PORT));
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.set(key, String(value));
    });
  }
  
  return url.toString();
}

/**
 * Get stored auth token
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('rpa_token');
}

/**
 * Store auth token
 */
export function setAuthToken(token: string): void {
  localStorage.setItem('rpa_token', token);
}

/**
 * Clear auth token
 */
export function clearAuthToken(): void {
  localStorage.removeItem('rpa_token');
  localStorage.removeItem('rpa_user');
}

/**
 * Store user info
 */
export function setStoredUser(user: User): void {
  localStorage.setItem('rpa_user', JSON.stringify(user));
}

/**
 * Get stored user info
 */
export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null;
  const userStr = localStorage.getItem('rpa_user');
  return userStr ? JSON.parse(userStr) : null;
}

/**
 * API request helper
 */
async function request<T>(
  endpoint: string,
  options: {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
    body?: unknown;
    params?: Record<string, string | number | boolean>;
    requiresAuth?: boolean;
  } = {}
): Promise<T> {
  const { method = 'GET', body, params, requiresAuth = true } = options;
  
  const url = buildUrl(endpoint, params);
  const token = getAuthToken();
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  
  if (requiresAuth && token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const response = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(errorData.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

// ============================================================================
// AUTH API
// ============================================================================

export const authApi = {
  /**
   * Login with email and password
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await request<LoginResponse>('/auth/login', {
      method: 'POST',
      body: credentials,
      requiresAuth: false,
    });
    
    // Store token and user
    setAuthToken(response.access_token);
    setStoredUser(response.user);
    
    return response;
  },
  
  /**
   * Register a new user
   */
  async register(data: RegisterRequest): Promise<APIResponse<User>> {
    return request<APIResponse<User>>('/auth/register', {
      method: 'POST',
      body: data,
      requiresAuth: false,
    });
  },
  
  /**
   * Logout and invalidate token
   */
  async logout(): Promise<void> {
    try {
      await request('/auth/logout', { method: 'POST' });
    } finally {
      clearAuthToken();
    }
  },
  
  /**
   * Refresh auth token
   */
  async refreshToken(): Promise<{ access_token: string }> {
    const response = await request<{ access_token: string }>('/auth/refresh', {
      method: 'POST',
    });
    setAuthToken(response.access_token);
    return response;
  },
};

// ============================================================================
// USER API
// ============================================================================

export const userApi = {
  /**
   * Get current user info
   */
  async me(): Promise<APIResponse<User>> {
    return request<APIResponse<User>>('/users/me');
  },
  
  /**
   * Update user preferences
   */
  async updatePreferences(preferences: Partial<User['preferences']>): Promise<{ message: string }> {
    return request('/users/me/preferences', {
      method: 'PUT',
      body: preferences,
    });
  },
  
  /**
   * Get user theme settings
   */
  async getTheme(): Promise<{
    role: string;
    theme: Record<string, unknown>;
    design_tokens: DesignTokens;
  }> {
    return request('/users/me/theme');
  },
};

// ============================================================================
// DASHBOARD API
// ============================================================================

export const dashboardApi = {
  /**
   * Get dashboard data
   */
  async get(): Promise<DashboardData> {
    return request<DashboardData>('/dashboard');
  },
  
  /**
   * Get learning progress
   */
  async getProgress(): Promise<LearningProgress> {
    return request<LearningProgress>('/progress');
  },
  
  /**
   * Get streak info
   */
  async getStreak(): Promise<{ current_streak: number; longest_streak: number }> {
    return request('/progress/streak');
  },
};

// ============================================================================
// VOCABULARY API
// ============================================================================

export const vocabularyApi = {
  /**
   * Get due vocabulary items
   */
  async getDue(limit: number = 20): Promise<{ items: VocabularyItem[]; count: number }> {
    return request('/vocabulary/due', { params: { limit } });
  },
  
  /**
   * Get new vocabulary items
   */
  async getNew(limit: number = 10): Promise<{ items: VocabularyItem[]; count: number }> {
    return request('/vocabulary/new', { params: { limit } });
  },
  
  /**
   * Get vocabulary statistics
   */
  async getStatistics(): Promise<{
    total_words: number;
    by_proficiency: Record<string, number>;
    due_count: number;
  }> {
    return request('/vocabulary/statistics');
  },
  
  /**
   * Get specific vocabulary item
   */
  async get(wordId: string): Promise<VocabularyItem> {
    return request(`/vocabulary/${wordId}`);
  },
  
  /**
   * Get flashcard for vocabulary item
   */
  async getFlashcard(wordId: string): Promise<VocabularyFlashcard> {
    return request(`/vocabulary/${wordId}/flashcard`);
  },
  
  /**
   * Get multiple choice for vocabulary item
   */
  async getMultipleChoice(wordId: string, numOptions: number = 4): Promise<VocabularyMultipleChoice> {
    return request(`/vocabulary/${wordId}/multiple-choice`, { params: { num_options: numOptions } });
  },
  
  /**
   * Review a vocabulary item
   */
  async review(review: VocabularyReviewRequest): Promise<VocabularyReviewResponse> {
    return request('/vocabulary/review', {
      method: 'POST',
      body: review,
    });
  },
};

// ============================================================================
// GRAMMAR API
// ============================================================================

export const grammarApi = {
  /**
   * List grammar rules
   */
  async listRules(options?: {
    category?: string;
    minDifficulty?: number;
    maxDifficulty?: number;
  }): Promise<{ rules: GrammarExercise[]; count: number }> {
    const params: Record<string, number | string> = {};
    if (options?.minDifficulty) params.min_difficulty = options.minDifficulty;
    if (options?.maxDifficulty) params.max_difficulty = options.maxDifficulty;
    
    return request('/grammar/rules', { params });
  },
  
  /**
   * Get specific grammar rule
   */
  async getRule(ruleId: string): Promise<GrammarExercise> {
    return request(`/grammar/rules/${ruleId}`);
  },
  
  /**
   * Get grammar exercise
   */
  async getExercise(request: GrammarExerciseRequest): Promise<GrammarExercise> {
    return request('/grammar/exercise', {
      method: 'POST',
      body: request,
    });
  },
  
  /**
   * Check text for grammar errors
   */
  async check(request: GrammarCheckRequest): Promise<GrammarCheckResponse> {
    return request('/grammar/check', {
      method: 'POST',
      body: request,
    });
  },
};

// ============================================================================
// LEARNING SESSION API
// ============================================================================

export const sessionApi = {
  /**
   * Create a new learning session
   */
  async create(domain: string = 'english', exerciseType: string = 'flashcard'): Promise<{
    success: boolean;
    message: string;
    data: {
      session_id: string;
      user_id: string;
      domain: string;
      exercise_type: string;
      started_at: string;
    };
  }> {
    return request('/learning/sessions', {
      method: 'POST',
      params: { domain, exercise_type: exerciseType },
    });
  },
  
  /**
   * Get session status
   */
  async get(sessionId: string): Promise<unknown> {
    return request(`/learning/sessions/${sessionId}`);
  },
  
  /**
   * Complete a learning session
   */
  async complete(sessionId: string): Promise<{ message: string }> {
    return request(`/learning/sessions/${sessionId}/complete`, {
      method: 'POST',
    });
  },
};

// ============================================================================
// ADMIN API
// ============================================================================

export const adminApi = {
  /**
   * List all users (admin+)
   */
  async listUsers(): Promise<{ users: User[]; count: number }> {
    return request('/admin/users');
  },
  
  /**
   * Update a user (admin+)
   */
  async updateUser(email: string, updates: AdminUserUpdate): Promise<{ message: string; user: User }> {
    return request(`/admin/users/${encodeURIComponent(email)}`, {
      method: 'PUT',
      body: updates,
    });
  },
  
  /**
   * Delete a user (superadmin only)
   */
  async deleteUser(email: string): Promise<{ message: string }> {
    return request(`/admin/users/${encodeURIComponent(email)}`, {
      method: 'DELETE',
    });
  },
  
  /**
   * List active sessions (admin+)
   */
  async listSessions(): Promise<{ sessions: unknown[]; count: number }> {
    return request('/admin/sessions');
  },
  
  /**
   * Get admin reports
   */
  async getReports(reportType: string = 'summary'): Promise<{
    report_type: string;
    generated_at: string;
    data: Record<string, unknown>;
  }> {
    return request('/admin/reports', { params: { report_type: reportType } });
  },
};

// ============================================================================
// SYSTEM API
// ============================================================================

export const systemApi = {
  /**
   * Health check (no auth required)
   */
  async health(): Promise<{ status: string; service: string }> {
    return request('/health', { requiresAuth: false });
  },
  
  /**
   * Get system status
   */
  async status(): Promise<{
    status: string;
    version: string;
    stm_patterns: number;
    ltm_patterns: number;
    total_users: number;
    active_users: number;
    domains: string[];
  }> {
    return request('/status');
  },
  
  /**
   * Get design tokens
   */
  async getDesignTokens(platform: 'web' | 'terminal' = 'web'): Promise<DesignTokens> {
    return request('/design-tokens', { params: { platform } });
  },
};

// ============================================================================
// EXPORT
// ============================================================================

export const api = {
  auth: authApi,
  user: userApi,
  dashboard: dashboardApi,
  vocabulary: vocabularyApi,
  grammar: grammarApi,
  session: sessionApi,
  admin: adminApi,
  system: systemApi,
};

export default api;
