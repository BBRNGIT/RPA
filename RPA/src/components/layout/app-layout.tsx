'use client';

/**
 * Main App Layout Component
 */

import { useEffect } from 'react';
import { useAuthStore, useAppStore } from '@/lib/stores';
import { Sidebar } from './sidebar';
import { Header } from './header';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const { isAuthenticated, checkAuth, user } = useAuthStore();
  const { sidebarCollapsed } = useAppStore();
  
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);
  
  // Not authenticated - show minimal layout
  if (!isAuthenticated || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-muted">
        {children}
      </div>
    );
  }
  
  // Authenticated - show full layout with sidebar
  return (
    <div className="flex h-screen bg-background">
      <Sidebar />
      
      <main className={cn(
        'flex-1 flex flex-col overflow-hidden transition-all duration-300',
      )}>
        <Header />
        
        <div className="flex-1 overflow-auto p-6">
          {children}
        </div>
      </main>
    </div>
  );
}

// Helper to replicate cn utility since we're in a client component
function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(' ');
}
