'use client';

/**
 * Settings Component
 * 
 * User preferences and application settings.
 */

import { useState } from 'react';
import { useAuthStore } from '@/lib/stores';
import { api } from '@/lib/api/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { 
  Settings as SettingsIcon, 
  User, 
  Bell, 
  Palette, 
  Save,
  Loader2,
} from 'lucide-react';
import type { UserPreferences } from '@/lib/api/types';

export function Settings() {
  const { user, refreshUser } = useAuthStore();
  const [saving, setSaving] = useState(false);
  const [preferences, setPreferences] = useState<Partial<UserPreferences>>(
    user?.preferences || {}
  );
  
  const handleSave = async () => {
    setSaving(true);
    try {
      await api.user.updatePreferences(preferences);
      await refreshUser();
    } catch (error) {
      console.error('Failed to save preferences:', error);
    } finally {
      setSaving(false);
    }
  };
  
  const updatePreference = <K extends keyof UserPreferences>(
    key: K,
    value: UserPreferences[K]
  ) => {
    setPreferences((prev) => ({ ...prev, [key]: value }));
  };
  
  if (!user) return null;
  
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your account and preferences
        </p>
      </div>
      
      {/* Profile Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <User className="w-5 h-5" />
            <CardTitle>Profile</CardTitle>
          </div>
          <CardDescription>
            Your account information
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Username</Label>
              <Input value={user.username} disabled />
            </div>
            <div className="space-y-2">
              <Label>Email</Label>
              <Input value={user.email} disabled />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Label>Role</Label>
            <Badge variant="secondary" className="capitalize">{user.role}</Badge>
          </div>
        </CardContent>
      </Card>
      
      {/* Learning Preferences */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <SettingsIcon className="w-5 h-5" />
            <CardTitle>Learning Preferences</CardTitle>
          </div>
          <CardDescription>
            Customize your learning experience
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Daily Goal</Label>
              <p className="text-sm text-muted-foreground">
                Number of items to learn each day
              </p>
            </div>
            <Input
              type="number"
              className="w-24"
              value={preferences.daily_goal || 30}
              onChange={(e) => updatePreference('daily_goal', parseInt(e.target.value) || 30)}
              min={5}
              max={200}
            />
          </div>
          
          <Separator />
          
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Difficulty</Label>
              <p className="text-sm text-muted-foreground">
                Learning difficulty level
              </p>
            </div>
            <Select
              value={preferences.difficulty || 'adaptive'}
              onValueChange={(value) => updatePreference('difficulty', value as UserPreferences['difficulty'])}
            >
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="easy">Easy</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="hard">Hard</SelectItem>
                <SelectItem value="adaptive">Adaptive</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      
      {/* Notifications */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5" />
            <CardTitle>Notifications</CardTitle>
          </div>
          <CardDescription>
            Control how you receive notifications
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Push Notifications</Label>
              <p className="text-sm text-muted-foreground">
                Receive reminders to study
              </p>
            </div>
            <Switch
              checked={preferences.notifications ?? true}
              onCheckedChange={(checked) => updatePreference('notifications', checked)}
            />
          </div>
          
          <Separator />
          
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Sound Effects</Label>
              <p className="text-sm text-muted-foreground">
                Play sounds during learning
              </p>
            </div>
            <Switch
              checked={preferences.sound_effects ?? true}
              onCheckedChange={(checked) => updatePreference('sound_effects', checked)}
            />
          </div>
        </CardContent>
      </Card>
      
      {/* Appearance */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Palette className="w-5 h-5" />
            <CardTitle>Appearance</CardTitle>
          </div>
          <CardDescription>
            Customize how the app looks
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Theme</Label>
              <p className="text-sm text-muted-foreground">
                Choose your preferred theme
              </p>
            </div>
            <Select
              value={preferences.theme || 'auto'}
              onValueChange={(value) => updatePreference('theme', value as UserPreferences['theme'])}
            >
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="light">Light</SelectItem>
                <SelectItem value="dark">Dark</SelectItem>
                <SelectItem value="auto">Auto</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <Separator />
          
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Font Size</Label>
              <p className="text-sm text-muted-foreground">
                Adjust text size
              </p>
            </div>
            <Input
              type="number"
              className="w-24"
              value={preferences.font_size || 16}
              onChange={(e) => updatePreference('font_size', parseInt(e.target.value) || 16)}
              min={10}
              max={32}
            />
          </div>
          
          <Separator />
          
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>Reduced Motion</Label>
              <p className="text-sm text-muted-foreground">
                Minimize animations
              </p>
            </div>
            <Switch
              checked={preferences.reduced_motion ?? false}
              onCheckedChange={(checked) => updatePreference('reduced_motion', checked)}
            />
          </div>
        </CardContent>
      </Card>
      
      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={saving}>
          {saving ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4 mr-2" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
