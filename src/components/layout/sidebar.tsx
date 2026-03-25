'use client';

/**
 * Sidebar Navigation Component
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthStore, useAppStore, isAdmin } from '@/lib/stores';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  LayoutDashboard,
  BookOpen,
  SpellCheck,
  FileText,
  PenTool,
  Settings,
  Users,
  ChevronLeft,
  ChevronRight,
  GraduationCap,
  Brain,
  Sparkles,
  MessageSquare,
} from 'lucide-react';

interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
  href: string;
  adminOnly?: boolean;
}

const navItems: NavItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
    href: '/?view=dashboard',
  },
  {
    id: 'llm-chat',
    label: 'LLM Chat',
    icon: MessageSquare,
    href: '/?view=llm-chat',
  },
  {
    id: 'si-dashboard',
    label: 'Self-Improvement',
    icon: Sparkles,
    href: '/?view=si-dashboard',
  },
  {
    id: 'vocabulary',
    label: 'Vocabulary',
    icon: BookOpen,
    href: '/?view=vocabulary',
  },
  {
    id: 'grammar',
    label: 'Grammar',
    icon: SpellCheck,
    href: '/?view=grammar',
  },
  {
    id: 'reading',
    label: 'Reading',
    icon: FileText,
    href: '/?view=reading',
  },
  {
    id: 'writing',
    label: 'Writing',
    icon: PenTool,
    href: '/?view=writing',
  },
  {
    id: 'admin',
    label: 'Admin Panel',
    icon: Users,
    href: '/?view=admin',
    adminOnly: true,
  },
];

const bottomNavItems: NavItem[] = [
  {
    id: 'settings',
    label: 'Settings',
    icon: Settings,
    href: '/?view=settings',
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuthStore();
  const { sidebarCollapsed, toggleSidebar } = useAppStore();
  
  const isCollapsed = sidebarCollapsed;
  const userIsAdmin = isAdmin(user);
  
  const filteredNavItems = navItems.filter(
    (item) => !item.adminOnly || userIsAdmin
  );
  
  return (
    <aside
      className={cn(
        'flex flex-col h-full bg-muted/30 border-r transition-all duration-300',
        isCollapsed ? 'w-16' : 'w-64'
      )}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-primary text-primary-foreground">
            <Brain className="w-6 h-6" />
          </div>
          {!isCollapsed && (
            <div className="flex flex-col">
              <span className="font-bold text-lg">RPA</span>
              <span className="text-xs text-muted-foreground">Learning System</span>
            </div>
          )}
        </div>
      </div>
      
      {/* Main Navigation */}
      <ScrollArea className="flex-1 py-4">
        <nav className="px-2 space-y-1">
          {filteredNavItems.map((item) => {
            const isActive = pathname === item.href || 
              (item.id !== 'dashboard' && pathname.includes(`view=${item.id}`));
            
            return (
              <Link
                key={item.id}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
                  'hover:bg-muted',
                  isActive
                    ? 'bg-primary/10 text-primary font-medium'
                    : 'text-muted-foreground',
                  isCollapsed && 'justify-center'
                )}
                title={isCollapsed ? item.label : undefined}
              >
                <item.icon className="w-5 h-5 shrink-0" />
                {!isCollapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>
      </ScrollArea>
      
      {/* Bottom Section */}
      <div className="mt-auto border-t">
        <div className="px-2 py-2 space-y-1">
          {bottomNavItems.map((item) => (
            <Link
              key={item.id}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-lg transition-colors',
                'hover:bg-muted text-muted-foreground',
                isCollapsed && 'justify-center'
              )}
              title={isCollapsed ? item.label : undefined}
            >
              <item.icon className="w-5 h-5 shrink-0" />
              {!isCollapsed && <span>{item.label}</span>}
            </Link>
          ))}
        </div>
        
        <Separator />
        
        {/* Collapse Toggle */}
        <div className="p-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleSidebar}
            className={cn('w-full', isCollapsed && 'justify-center')}
          >
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <>
                <ChevronLeft className="w-4 h-4 mr-2" />
                <span>Collapse</span>
              </>
            )}
          </Button>
        </div>
        
        {/* User Info */}
        {!isCollapsed && user && (
          <div className="px-4 py-3 border-t">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary">
                <GraduationCap className="w-4 h-4" />
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-sm font-medium truncate">
                  {user.username}
                </span>
                <span className="text-xs text-muted-foreground capitalize">
                  {user.role}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
