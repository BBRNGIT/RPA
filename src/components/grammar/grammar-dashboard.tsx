'use client';

/**
 * Grammar Dashboard Component
 */

import { useState, useEffect } from 'react';
import { api } from '@/lib/api/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  SpellCheck, 
  FileCheck, 
  AlertCircle,
  CheckCircle,
  Loader2,
} from 'lucide-react';
import type { GrammarExercise, GrammarCheckResponse } from '@/lib/api/types';

export function GrammarDashboard() {
  const [loading, setLoading] = useState(false);
  const [checkingText, setCheckingText] = useState('');
  const [checkResult, setCheckResult] = useState<GrammarCheckResponse | null>(null);
  const [currentExercise, setCurrentExercise] = useState<GrammarExercise | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  
  const handleCheckGrammar = async () => {
    if (!checkingText.trim()) return;
    
    setLoading(true);
    try {
      const result = await api.grammar.check({ text: checkingText });
      setCheckResult(result);
    } catch (error) {
      console.error('Failed to check grammar:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const loadExercise = async () => {
    setLoading(true);
    try {
      const exercise = await api.grammar.getExercise({
        exercise_type: 'multiple_choice',
        difficulty: 2,
      });
      setCurrentExercise(exercise);
      setSelectedAnswer(null);
      setShowExplanation(false);
    } catch (error) {
      console.error('Failed to load exercise:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleAnswer = (answer: string) => {
    setSelectedAnswer(answer);
    setShowExplanation(true);
  };
  
  useEffect(() => {
    loadExercise();
  }, []);
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Grammar</h1>
        <p className="text-muted-foreground mt-1">
          Practice grammar rules and check your writing
        </p>
      </div>
      
      {/* Tabs */}
      <Tabs defaultValue="exercise">
        <TabsList>
          <TabsTrigger value="exercise">
            <SpellCheck className="w-4 h-4 mr-2" />
            Exercises
          </TabsTrigger>
          <TabsTrigger value="check">
            <FileCheck className="w-4 h-4 mr-2" />
            Grammar Check
          </TabsTrigger>
        </TabsList>
        
        {/* Exercise Tab */}
        <TabsContent value="exercise" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Exercise Card */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Grammar Exercise</CardTitle>
                  <Button variant="outline" size="sm" onClick={loadExercise}>
                    New Exercise
                  </Button>
                </div>
                <CardDescription>
                  Answer the question to practice grammar rules
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center justify-center h-48">
                    <Loader2 className="w-8 h-8 animate-spin" />
                  </div>
                ) : currentExercise ? (
                  <div className="space-y-4">
                    <div className="p-4 bg-muted rounded-lg">
                      <p className="text-lg">{currentExercise.question}</p>
                    </div>
                    
                    {currentExercise.options ? (
                      <div className="space-y-2">
                        {currentExercise.options.map((option, index) => {
                          const isSelected = selectedAnswer === option;
                          const isCorrect = option === currentExercise.correct_answer;
                          
                          return (
                            <Button
                              key={index}
                              variant={isSelected ? (isCorrect ? 'default' : 'destructive') : 'outline'}
                              className="w-full justify-start"
                              onClick={() => handleAnswer(option)}
                              disabled={!!selectedAnswer}
                            >
                              {isSelected && (
                                isCorrect ? (
                                  <CheckCircle className="w-4 h-4 mr-2" />
                                ) : (
                                  <AlertCircle className="w-4 h-4 mr-2" />
                                )
                              )}
                              {option}
                            </Button>
                          );
                        })}
                      </div>
                    ) : null}
                    
                    {showExplanation && (
                      <div className={`p-4 rounded-lg ${selectedAnswer === currentExercise.correct_answer ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                        <p className="font-medium mb-2">
                          {selectedAnswer === currentExercise.correct_answer ? 'Correct!' : 'Incorrect'}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {currentExercise.explanation}
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No exercise loaded
                  </div>
                )}
              </CardContent>
            </Card>
            
            {/* Rules Reference */}
            <Card>
              <CardHeader>
                <CardTitle>Grammar Rules</CardTitle>
                <CardDescription>
                  Common rules to remember
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 text-sm">
                  <div className="p-3 bg-muted rounded-lg">
                    <p className="font-medium">Subject-Verb Agreement</p>
                    <p className="text-muted-foreground">A singular subject takes a singular verb.</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg">
                    <p className="font-medium">Tense Consistency</p>
                    <p className="text-muted-foreground">Keep verb tenses consistent within sentences.</p>
                  </div>
                  <div className="p-3 bg-muted rounded-lg">
                    <p className="font-medium">Article Usage</p>
                    <p className="text-muted-foreground">Use 'a/an' for indefinite, 'the' for definite nouns.</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        {/* Grammar Check Tab */}
        <TabsContent value="check" className="mt-6">
          <Card className="max-w-2xl mx-auto">
            <CardHeader>
              <CardTitle>Grammar Checker</CardTitle>
              <CardDescription>
                Paste your text to check for grammar errors
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Textarea
                placeholder="Type or paste your text here..."
                value={checkingText}
                onChange={(e) => setCheckingText(e.target.value)}
                rows={6}
              />
              
              <Button onClick={handleCheckGrammar} disabled={loading || !checkingText.trim()}>
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Checking...
                  </>
                ) : (
                  <>
                    <SpellCheck className="w-4 h-4 mr-2" />
                    Check Grammar
                  </>
                )}
              </Button>
              
              {checkResult && (
                <div className="space-y-4 pt-4 border-t">
                  <div className="flex items-center gap-4">
                    <span className="text-sm font-medium">Score:</span>
                    <Progress value={checkResult.score * 100} className="flex-1" />
                    <Badge variant={checkResult.score > 0.8 ? 'default' : 'secondary'}>
                      {Math.round(checkResult.score * 100)}%
                    </Badge>
                  </div>
                  
                  {checkResult.errors.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Issues found:</p>
                      {checkResult.errors.map((error, index) => (
                        <div key={index} className="p-3 bg-destructive/10 rounded-lg">
                          <p className="text-sm">{error.message}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            Suggestion: {error.suggestion}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {checkResult.suggestions.length > 0 && (
                    <div className="space-y-2">
                      <p className="text-sm font-medium">Suggestions:</p>
                      <ul className="text-sm text-muted-foreground list-disc list-inside">
                        {checkResult.suggestions.map((s, i) => (
                          <li key={i}>{s}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
