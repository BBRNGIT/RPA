'use client';

/**
 * Vocabulary Dashboard Component
 * 
 * Main vocabulary learning interface with flashcards and statistics.
 */

import { useEffect, useState } from 'react';
import { useAppStore } from '@/lib/stores';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  BookOpen, 
  ChevronLeft, 
  ChevronRight, 
  RotateCcw,
  ThumbsUp,
  ThumbsDown,
  Minus,
  Sparkles,
  Clock,
  Target,
  Loader2,
} from 'lucide-react';
import type { VocabularyFlashcard } from '@/lib/api/types';

export function VocabularyDashboard() {
  const {
    currentVocabItems,
    currentFlashcard,
    currentCardIndex,
    showBack,
    isVocabLoading,
    vocabMode,
    loadDueVocabulary,
    loadNewVocabulary,
    nextCard,
    previousCard,
    flipCard,
    reviewCard,
    setVocabMode,
    startSession,
    endSession,
    activeSessionId,
  } = useAppStore();
  
  const [sessionStarted, setSessionStarted] = useState(false);
  
  useEffect(() => {
    if (!activeSessionId && sessionStarted) {
      startSession('english', 'flashcard');
    }
  }, [activeSessionId, sessionStarted, startSession]);
  
  // Load due vocabulary on mount
  useEffect(() => {
    loadDueVocabulary(20);
  }, [loadDueVocabulary]);
  
  const handleStartSession = async () => {
    await loadDueVocabulary(20);
    await startSession('english', 'flashcard');
    setSessionStarted(true);
  };
  
  const handleReview = async (quality: number) => {
    await reviewCard(quality);
  };
  
  // Loading state
  if (isVocabLoading && currentVocabItems.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }
  
  // No items to review
  if (!isVocabLoading && currentVocabItems.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Vocabulary</h1>
            <p className="text-muted-foreground mt-1">
              Learn and review vocabulary with spaced repetition
            </p>
          </div>
        </div>
        
        <Card className="max-w-lg mx-auto">
          <CardContent className="pt-6 text-center">
            <BookOpen className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
            <h3 className="text-xl font-semibold mb-2">All caught up!</h3>
            <p className="text-muted-foreground mb-6">
              You have no vocabulary items due for review right now.
              Check back later or learn new words.
            </p>
            <Button onClick={() => loadNewVocabulary(10)}>
              <Sparkles className="w-4 h-4 mr-2" />
              Learn New Words
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Vocabulary</h1>
          <p className="text-muted-foreground mt-1">
            Learn and review vocabulary with spaced repetition
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary">
            {currentCardIndex + 1} / {currentVocabItems.length}
          </Badge>
        </div>
      </div>
      
      {/* Tabs for different modes */}
      <Tabs value={vocabMode} onValueChange={(v) => setVocabMode(v as 'flashcard' | 'multiple-choice' | 'list')}>
        <TabsList>
          <TabsTrigger value="flashcard">Flashcards</TabsTrigger>
          <TabsTrigger value="multiple-choice">Multiple Choice</TabsTrigger>
          <TabsTrigger value="list">Word List</TabsTrigger>
        </TabsList>
        
        <TabsContent value="flashcard" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Flashcard */}
            <div className="lg:col-span-2">
              {currentFlashcard && (
                <FlashcardView
                  flashcard={currentFlashcard}
                  showBack={showBack}
                  onFlip={flipCard}
                  onReview={handleReview}
                />
              )}
            </div>
            
            {/* Progress & Controls */}
            <div className="space-y-4">
              {/* Progress Card */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Session Progress</CardTitle>
                </CardHeader>
                <CardContent>
                  <Progress 
                    value={((currentCardIndex + 1) / currentVocabItems.length) * 100} 
                    className="h-2"
                  />
                  <div className="flex justify-between text-xs text-muted-foreground mt-2">
                    <span>Reviewed: {currentCardIndex}</span>
                    <span>Remaining: {currentVocabItems.length - currentCardIndex - 1}</span>
                  </div>
                </CardContent>
              </Card>
              
              {/* Navigation */}
              <Card>
                <CardContent className="pt-4">
                  <div className="flex justify-between gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={previousCard}
                      disabled={currentCardIndex === 0}
                    >
                      <ChevronLeft className="w-4 h-4 mr-1" />
                      Previous
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={nextCard}
                      disabled={currentCardIndex >= currentVocabItems.length - 1}
                    >
                      Next
                      <ChevronRight className="w-4 h-4 ml-1" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
              
              {/* Quick Actions */}
              <Card>
                <CardContent className="pt-4">
                  <div className="space-y-2">
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => loadDueVocabulary(20)}
                    >
                      <RotateCcw className="w-4 h-4 mr-2" />
                      Reload Due Words
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start"
                      onClick={() => loadNewVocabulary(10)}
                    >
                      <Sparkles className="w-4 h-4 mr-2" />
                      Learn New Words
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>
        
        <TabsContent value="multiple-choice" className="mt-6">
          <Card className="max-w-2xl mx-auto">
            <CardContent className="pt-6 text-center">
              <Target className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Multiple Choice Mode</h3>
              <p className="text-muted-foreground">
                Test your knowledge with multiple choice questions.
                This mode is coming soon!
              </p>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="list" className="mt-6">
          <Card className="max-w-2xl mx-auto">
            <CardContent className="pt-6 text-center">
              <BookOpen className="w-16 h-16 mx-auto text-muted-foreground/50 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Word List Mode</h3>
              <p className="text-muted-foreground">
                Browse and study your vocabulary in list format.
                This mode is coming soon!
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

// Flashcard View Component
function FlashcardView({
  flashcard,
  showBack,
  onFlip,
  onReview,
}: {
  flashcard: VocabularyFlashcard;
  showBack: boolean;
  onFlip: () => void;
  onReview: (quality: number) => void;
}) {
  return (
    <div className="space-y-4">
      {/* Card */}
      <Card 
        className="min-h-[300px] cursor-pointer hover:shadow-lg transition-shadow"
        onClick={onFlip}
      >
        <CardContent className="flex flex-col items-center justify-center min-h-[280px] p-8">
          {!showBack ? (
            // Front - Word
            <div className="text-center">
              <Badge variant="outline" className="mb-4">
                {flashcard.part_of_speech}
              </Badge>
              <h2 className="text-4xl font-bold mb-4">{flashcard.front}</h2>
              {flashcard.hint && (
                <p className="text-muted-foreground text-sm">
                  Hint: {flashcard.hint}
                </p>
              )}
              <p className="text-muted-foreground text-sm mt-4">
                Click to reveal definition
              </p>
            </div>
          ) : (
            // Back - Definition
            <div className="text-center">
              <h2 className="text-2xl font-semibold mb-4">{flashcard.front}</h2>
              <p className="text-lg text-muted-foreground mb-6">{flashcard.back}</p>
              {flashcard.examples.length > 0 && (
                <div className="text-left bg-muted/50 rounded-lg p-4 mb-4">
                  <p className="text-xs text-muted-foreground mb-2">Examples:</p>
                  {flashcard.examples.slice(0, 2).map((ex, i) => (
                    <p key={i} className="text-sm italic">"{ex}"</p>
                  ))}
                </div>
              )}
              <div className="flex items-center justify-center gap-1">
                {[...Array(flashcard.difficulty)].map((_, i) => (
                  <span key={i} className="text-yellow-500">★</span>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Quality Rating Buttons (only show when back is visible) */}
      {showBack && (
        <div className="flex justify-center gap-2">
          <Button 
            variant="outline" 
            className="flex-1 max-w-[120px]"
            onClick={() => onReview(1)}
          >
            <ThumbsDown className="w-4 h-4 mr-2 text-red-500" />
            Again
          </Button>
          <Button 
            variant="outline" 
            className="flex-1 max-w-[120px]"
            onClick={() => onReview(3)}
          >
            <Minus className="w-4 h-4 mr-2 text-yellow-500" />
            Hard
          </Button>
          <Button 
            variant="outline" 
            className="flex-1 max-w-[120px]"
            onClick={() => onReview(4)}
          >
            <ThumbsUp className="w-4 h-4 mr-2 text-green-500" />
            Good
          </Button>
          <Button 
            variant="outline" 
            className="flex-1 max-w-[120px]"
            onClick={() => onReview(5)}
          >
            <Sparkles className="w-4 h-4 mr-2 text-blue-500" />
            Easy
          </Button>
        </div>
      )}
    </div>
  );
}
