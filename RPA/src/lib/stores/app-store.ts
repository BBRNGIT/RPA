/**
 * Application Store
 * 
 * Zustand store for managing application-wide state including
 * learning sessions, current view, and UI preferences.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  VocabularyItem,
  VocabularyFlashcard,
  DashboardData,
  LearningProgress,
} from '@/lib/api/types';
import { api } from '@/lib/api/client';

// ============================================================================
// TYPES
// ============================================================================

type ViewType = 'dashboard' | 'vocabulary' | 'grammar' | 'reading' | 'writing' | 'admin' | 'settings';
type VocabMode = 'flashcard' | 'multiple-choice' | 'list';

interface AppState {
  // Current view
  currentView: ViewType;
  setCurrentView: (view: ViewType) => void;
  
  // Dashboard data
  dashboard: DashboardData | null;
  dashboardLoading: boolean;
  loadDashboard: () => Promise<void>;
  
  // Progress
  progress: LearningProgress | null;
  progressLoading: boolean;
  loadProgress: () => Promise<void>;
  
  // Vocabulary state
  vocabMode: VocabMode;
  setVocabMode: (mode: VocabMode) => void;
  
  currentVocabItems: VocabularyItem[];
  currentFlashcard: VocabularyFlashcard | null;
  currentCardIndex: number;
  showBack: boolean;
  
  loadDueVocabulary: (limit?: number) => Promise<void>;
  loadNewVocabulary: (limit?: number) => Promise<void>;
  loadFlashcard: (wordId: string) => Promise<void>;
  nextCard: () => void;
  previousCard: () => void;
  flipCard: () => void;
  reviewCard: (quality: number) => Promise<void>;
  
  // Session state
  activeSessionId: string | null;
  sessionStartTime: number | null;
  startSession: (domain: string, exerciseType: string) => Promise<string | null>;
  endSession: () => Promise<void>;
  
  // UI preferences
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;
  
  // Loading states
  isVocabLoading: boolean;
  
  // Error handling
  error: string | null;
  setError: (error: string | null) => void;
  clearError: () => void;
}

// ============================================================================
// STORE
// ============================================================================

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // View state
      currentView: 'dashboard',
      setCurrentView: (view) => set({ currentView: view }),
      
      // Dashboard
      dashboard: null,
      dashboardLoading: false,
      loadDashboard: async () => {
        set({ dashboardLoading: true });
        try {
          const data = await api.dashboard.get();
          set({ dashboard: data, dashboardLoading: false });
        } catch (error) {
          console.error('Failed to load dashboard:', error);
          set({ dashboardLoading: false });
        }
      },
      
      // Progress
      progress: null,
      progressLoading: false,
      loadProgress: async () => {
        set({ progressLoading: true });
        try {
          const data = await api.dashboard.getProgress();
          set({ progress: data, progressLoading: false });
        } catch (error) {
          console.error('Failed to load progress:', error);
          set({ progressLoading: false });
        }
      },
      
      // Vocabulary mode
      vocabMode: 'flashcard',
      setVocabMode: (mode) => set({ vocabMode: mode }),
      
      // Vocabulary items
      currentVocabItems: [],
      currentFlashcard: null,
      currentCardIndex: 0,
      showBack: false,
      
      loadDueVocabulary: async (limit = 20) => {
        set({ isVocabLoading: true });
        try {
          const { items } = await api.vocabulary.getDue(limit);
          set({ 
            currentVocabItems: items, 
            currentCardIndex: 0,
            showBack: false,
            isVocabLoading: false,
          });
          
          // Load first flashcard
          if (items.length > 0) {
            await get().loadFlashcard(items[0].word_id);
          }
        } catch (error) {
          console.error('Failed to load due vocabulary:', error);
          set({ isVocabLoading: false });
        }
      },
      
      loadNewVocabulary: async (limit = 10) => {
        set({ isVocabLoading: true });
        try {
          const { items } = await api.vocabulary.getNew(limit);
          set({ 
            currentVocabItems: items, 
            currentCardIndex: 0,
            showBack: false,
            isVocabLoading: false,
          });
          
          if (items.length > 0) {
            await get().loadFlashcard(items[0].word_id);
          }
        } catch (error) {
          console.error('Failed to load new vocabulary:', error);
          set({ isVocabLoading: false });
        }
      },
      
      loadFlashcard: async (wordId) => {
        try {
          const flashcard = await api.vocabulary.getFlashcard(wordId);
          set({ currentFlashcard: flashcard, showBack: false });
        } catch (error) {
          console.error('Failed to load flashcard:', error);
        }
      },
      
      nextCard: () => {
        const { currentCardIndex, currentVocabItems } = get();
        if (currentCardIndex < currentVocabItems.length - 1) {
          const newIndex = currentCardIndex + 1;
          set({ currentCardIndex: newIndex, showBack: false });
          get().loadFlashcard(currentVocabItems[newIndex].word_id);
        }
      },
      
      previousCard: () => {
        const { currentCardIndex, currentVocabItems } = get();
        if (currentCardIndex > 0) {
          const newIndex = currentCardIndex - 1;
          set({ currentCardIndex: newIndex, showBack: false });
          get().loadFlashcard(currentVocabItems[newIndex].word_id);
        }
      },
      
      flipCard: () => set((state) => ({ showBack: !state.showBack })),
      
      reviewCard: async (quality) => {
        const { currentVocabItems, currentCardIndex, sessionStartTime } = get();
        const item = currentVocabItems[currentCardIndex];
        
        if (!item) return;
        
        try {
          const timeSpent = sessionStartTime 
            ? (Date.now() - sessionStartTime) / 1000 
            : 0;
          
          await api.vocabulary.review({
            word_id: item.word_id,
            quality,
            response: '',
            time_spent_seconds: timeSpent,
          });
          
          // Move to next card
          get().nextCard();
        } catch (error) {
          console.error('Failed to review card:', error);
        }
      },
      
      // Session
      activeSessionId: null,
      sessionStartTime: null,
      startSession: async (domain, exerciseType) => {
        try {
          const response = await api.session.create(domain, exerciseType);
          if (response.data) {
            set({ 
              activeSessionId: response.data.session_id,
              sessionStartTime: Date.now(),
            });
            return response.data.session_id;
          }
          return null;
        } catch (error) {
          console.error('Failed to start session:', error);
          return null;
        }
      },
      
      endSession: async () => {
        const { activeSessionId } = get();
        if (activeSessionId) {
          try {
            await api.session.complete(activeSessionId);
          } catch (error) {
            console.error('Failed to end session:', error);
          }
        }
        set({ activeSessionId: null, sessionStartTime: null });
      },
      
      // UI
      sidebarCollapsed: false,
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      
      // Loading
      isVocabLoading: false,
      
      // Errors
      error: null,
      setError: (error) => set({ error }),
      clearError: () => set({ error: null }),
    }),
    {
      name: 'rpa-app',
      partialize: (state) => ({
        currentView: state.currentView,
        sidebarCollapsed: state.sidebarCollapsed,
        vocabMode: state.vocabMode,
      }),
    }
  )
);
