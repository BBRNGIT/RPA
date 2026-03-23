'use client';

/**
 * RPA Learning System - Main Application Page
 * 
 * Single-page application with view-based routing.
 * All views are rendered based on the 'view' query parameter.
 */

import { Suspense, useEffect, useMemo, useState, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { useAuthStore, useAppStore } from '@/lib/stores';
import { AppLayout } from '@/components/layout';
import { LoginForm, RegisterForm } from '@/components/auth';
import { Dashboard } from '@/components/dashboard';
import { VocabularyDashboard } from '@/components/vocabulary';
import { GrammarDashboard } from '@/components/grammar';
import { AdminPanel, Settings } from '@/components/admin';
import { SIDashboard } from '@/components/si-dashboard';

type ViewType = 'dashboard' | 'si-dashboard' | 'vocabulary' | 'grammar' | 'reading' | 'writing' | 'admin' | 'settings';

// Placeholder for coming soon views
function ComingSoonView({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-2">{title}</h1>
        <p className="text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}

// Auth view component (separated to avoid setState in effect issues)
function AuthView() {
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  
  return (
    <AppLayout>
      <div className="w-full max-w-md">
        {authMode === 'login' ? (
          <LoginForm onSwitchToRegister={() => setAuthMode('register')} />
        ) : (
          <RegisterForm 
            onSwitchToLogin={() => setAuthMode('login')}
            onRegistered={() => setAuthMode('login')}
          />
        )}
      </div>
    </AppLayout>
  );
}

// Authenticated app view
function AuthenticatedApp({ currentView }: { currentView: ViewType }) {
  const { loadDashboard, loadProgress, setCurrentView } = useAppStore();
  
  // Load data on mount
  useEffect(() => {
    loadDashboard();
    loadProgress();
  }, [loadDashboard, loadProgress]);
  
  // Sync view state
  useEffect(() => {
    setCurrentView(currentView);
  }, [currentView, setCurrentView]);
  
  const renderView = useMemo(() => {
    switch (currentView) {
      case 'si-dashboard':
        return <SIDashboard />;
      case 'vocabulary':
        return <VocabularyDashboard />;
      case 'grammar':
        return <GrammarDashboard />;
      case 'admin':
        return <AdminPanel />;
      case 'settings':
        return <Settings />;
      case 'reading':
        return <ComingSoonView title="Reading" description="Reading comprehension exercises coming soon!" />;
      case 'writing':
        return <ComingSoonView title="Writing" description="Writing practice and assessment coming soon!" />;
      case 'dashboard':
      default:
        return <Dashboard />;
    }
  }, [currentView]);
  
  return (
    <AppLayout>
      {renderView}
    </AppLayout>
  );
}

// Inner component that uses useSearchParams (wrapped in Suspense)
function AppContent() {
  const searchParams = useSearchParams();
  const { isAuthenticated, checkAuth, user, isLoading } = useAuthStore();
  
  // Get current view from URL
  const viewParam = searchParams.get('view') as ViewType | null;
  const currentView: ViewType = viewParam || 'dashboard';
  
  // Check auth on mount - using a callback pattern
  const handleAuthCheck = useCallback(() => {
    checkAuth();
  }, [checkAuth]);
  
  useEffect(() => {
    handleAuthCheck();
  }, [handleAuthCheck]);
  
  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }
  
  // Not authenticated - show auth forms
  if (!isAuthenticated || !user) {
    return <AuthView />;
  }
  
  // Authenticated - show main app
  return <AuthenticatedApp currentView={currentView} />;
}

// Loading fallback for Suspense
function LoadingFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="animate-pulse text-muted-foreground">Loading...</div>
    </div>
  );
}

// Main page component with Suspense boundary
export default function Home() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <AppContent />
    </Suspense>
  );
}
