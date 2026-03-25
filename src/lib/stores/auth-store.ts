/**
 * Authentication Store
 * 
 * Zustand store for managing authentication state.
 * Syncs with localStorage for persistence across sessions.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '@/lib/api/types';
import { api, getStoredUser, setStoredUser, clearAuthToken, setAuthToken } from '@/lib/api/client';

interface AuthState {
  // State
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (email: string, password: string) => Promise<boolean>;
  register: (email: string, username: string, password: string) => Promise<boolean>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
  setUser: (user: User | null) => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      
      // Login action
      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.auth.login({ email, password });
          
          set({
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
          
          return true;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Login failed';
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: message,
          });
          return false;
        }
      },
      
      // Register action
      register: async (email: string, username: string, password: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.auth.register({ email, username, password });
          
          if (response.success && response.data) {
            // After registration, log the user in
            return get().login(email, password);
          }
          
          set({
            isLoading: false,
            error: response.message || 'Registration failed',
          });
          return false;
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Registration failed';
          set({
            isLoading: false,
            error: message,
          });
          return false;
        }
      },
      
      // Logout action
      logout: async () => {
        set({ isLoading: true });
        
        try {
          await api.auth.logout();
        } catch {
          // Clear auth even if API call fails
          clearAuthToken();
        }
        
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      },
      
      // Refresh user data
      refreshUser: async () => {
        if (!get().isAuthenticated) return;
        
        try {
          const response = await api.user.me();
          if (response.data) {
            set({ user: response.data });
            setStoredUser(response.data);
          }
        } catch (error) {
          // Token might be expired, logout
          if (error instanceof Error && error.message.includes('401')) {
            get().logout();
          }
        }
      },
      
      // Clear error
      clearError: () => set({ error: null }),
      
      // Set user directly
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      
      // Check if already authenticated (on app load)
      checkAuth: async () => {
        const storedUser = getStoredUser();
        
        if (storedUser) {
          set({ user: storedUser, isAuthenticated: true });
          
          // Verify token is still valid
          try {
            const response = await api.user.me();
            if (response.data) {
              set({ user: response.data });
              setStoredUser(response.data);
            }
          } catch {
            // Token invalid, clear state
            clearAuthToken();
            set({ user: null, isAuthenticated: false });
          }
        }
      },
    }),
    {
      name: 'rpa-auth',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Role-based permission helpers
export function hasRole(user: User | null, roles: string[]): boolean {
  if (!user) return false;
  return roles.includes(user.role);
}

export function isAdmin(user: User | null): boolean {
  return hasRole(user, ['admin', 'superadmin']);
}

export function isSuperAdmin(user: User | null): boolean {
  return hasRole(user, ['superadmin']);
}

export function canManageUsers(user: User | null): boolean {
  return isAdmin(user);
}

export function canAccessAdminPanel(user: User | null): boolean {
  return isAdmin(user);
}
