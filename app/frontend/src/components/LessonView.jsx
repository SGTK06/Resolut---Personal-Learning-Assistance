import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import {
    Loader2,
    ArrowLeft,
    CheckCircle2,
    XCircle,
    ChevronRight,
    BookOpen,
    HelpCircle
} from 'lucide-react';
import { API_BASE_URL } from '../api';

const LessonView = ({ topic, chapter, lesson, onBack, onComplete }) => {
    const [loading, setLoading] = useState(true);
    const [content, setContent] = useState(null);
    const [error, setError] = useState(null);

    // Modes: 'reading' | 'quiz' | 'completed'
    const [mode, setMode] = useState('reading');

    // Quiz State
    const [currentQuestionIdx, setCurrentQuestionIdx] = useState(0);
    const [selectedOption, setSelectedOption] = useState(null);
    const [isAnswered, setIsAnswered] = useState(false);
    const [isCorrect, setIsCorrect] = useState(false);

    useEffect(() => {
        const fetchLesson = async () => {
            setLoading(true);
            try {
                const response = await axios.post(`${API_BASE_URL}/api/lessons/start`, {
                    topic,
                    chapter,
                    lesson
                });
                setContent(response.data);
            } catch (err) {
                setError("Failed to load lesson content.");
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchLesson();
    }, [topic, chapter, lesson]);

    const handleOptionSelect = (idx) => {
        if (isAnswered) return;
        setSelectedOption(idx);
    };

    const handleSubmitAnswer = () => {
        if (selectedOption === null) return;

        const question = content.questions[currentQuestionIdx];
        const correct = selectedOption === question.correct_option_index;

        setIsAnswered(true);
        setIsCorrect(correct);
    };

    const handleNextQuestion = () => {
        if (currentQuestionIdx < content.questions.length - 1) {
            setCurrentQuestionIdx(prev => prev + 1);
            setSelectedOption(null);
            setIsAnswered(false);
            setIsCorrect(false);
        } else {
            // Quiz Finished
            setMode('completed');
        }
    };

    const handleFinish = () => {
        onComplete();
    };


    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center p-20 text-slate-400">
                <Loader2 className="w-10 h-10 animate-spin mb-4 text-cyan-500" />
                <p>Preparing your lesson...</p>
            </div>
        );
    }

    if (error || !content) {
        return (
            <div className="p-8 text-center text-red-500">
                <p>{error || "Lesson content not found."}</p>
                <button onClick={onBack} className="mt-4 text-blue-500 underline">Go Back</button>
            </div>
        );
    }

    return (
        <div className="max-w-3xl mx-auto pb-20 animate-fade-in text-slate-800 dark:text-slate-100">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <button
                    onClick={onBack}
                    className="flex items-center gap-2 text-slate-500 hover:text-cyan-600 transition-colors"
                >
                    <ArrowLeft size={20} />
                    <span>Back to Roadmap</span>
                </button>
                <div className="text-sm font-medium text-slate-400">
                    {chapter}
                </div>
            </div>

            {/* Reading Mode */}
            {mode === 'reading' && (
                <div className="space-y-8">
                    <div className="prose dark:prose-invert max-w-none bg-white dark:bg-slate-800 p-8 rounded-3xl border border-slate-200 dark:border-slate-700 shadow-sm">
                        <h1 className="text-3xl font-bold mb-6 text-cyan-900 dark:text-cyan-100">{content.lesson_title}</h1>
                        <ReactMarkdown>{content.content_markdown}</ReactMarkdown>
                    </div>

                    <button
                        onClick={() => setMode('quiz')}
                        className="w-full bg-cyan-600 text-white py-4 rounded-xl font-bold hover:bg-cyan-700 transition-all shadow-lg shadow-cyan-500/30 flex items-center justify-center gap-2"
                    >
                        <HelpCircle size={24} />
                        Start Quiz to Complete Lesson
                    </button>
                </div>
            )}

            {/* Quiz Mode */}
            {mode === 'quiz' && (
                <div className="max-w-2xl mx-auto">
                    <div className="mb-6 flex justify-between items-center text-sm font-medium text-slate-500">
                        <span>Question {currentQuestionIdx + 1} of {content.questions.length}</span>
                        <div className="flex gap-1">
                            {content.questions.map((_, idx) => (
                                <div
                                    key={idx}
                                    className={`w-8 h-2 rounded-full ${idx < currentQuestionIdx ? 'bg-cyan-500' :
                                            idx === currentQuestionIdx ? 'bg-cyan-200 dark:bg-cyan-800' : 'bg-slate-200 dark:bg-slate-700'
                                        }`}
                                />
                            ))}
                        </div>
                    </div>

                    <div className="bg-white dark:bg-slate-800 p-8 rounded-3xl border border-slate-200 dark:border-slate-700 shadow-lg">
                        <h3 className="text-xl font-bold mb-6">
                            {content.questions[currentQuestionIdx].question}
                        </h3>

                        <div className="space-y-3">
                            {content.questions[currentQuestionIdx].options.map((option, idx) => {
                                let stateStyle = "border-slate-200 dark:border-slate-600 hover:border-cyan-400";

                                if (isAnswered) {
                                    if (idx === content.questions[currentQuestionIdx].correct_option_index) {
                                        stateStyle = "bg-teal-50 dark:bg-teal-900/30 border-teal-500 text-teal-700 dark:text-teal-300";
                                    } else if (idx === selectedOption) {
                                        stateStyle = "bg-red-50 dark:bg-red-900/20 border-red-500 text-red-700 dark:text-red-300";
                                    } else {
                                        stateStyle = "opacity-50 border-slate-200 dark:border-slate-700";
                                    }
                                } else if (selectedOption === idx) {
                                    stateStyle = "border-cyan-500 bg-cyan-50 dark:bg-cyan-900/20 text-cyan-700 dark:text-cyan-300";
                                }

                                return (
                                    <button
                                        key={idx}
                                        onClick={() => handleOptionSelect(idx)}
                                        disabled={isAnswered}
                                        className={`w-full text-left p-4 rounded-xl border-2 transition-all font-medium flex items-center justify-between ${stateStyle}`}
                                    >
                                        <span>{option}</span>
                                        {isAnswered && idx === content.questions[currentQuestionIdx].correct_option_index && (
                                            <CheckCircle2 size={20} className="text-teal-500" />
                                        )}
                                        {isAnswered && idx === selectedOption && idx !== content.questions[currentQuestionIdx].correct_option_index && (
                                            <XCircle size={20} className="text-red-500" />
                                        )}
                                    </button>
                                );
                            })}
                        </div>

                        {/* Explanation & Next Button */}
                        {isAnswered && (
                            <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-700 animate-slide-down">
                                <div className={`p-4 rounded-xl mb-6 ${isCorrect ? 'bg-teal-50 dark:bg-teal-900/20' : 'bg-slate-50 dark:bg-slate-800'}`}>
                                    <p className="font-bold mb-1 flex items-center gap-2">
                                        {isCorrect ? (
                                            <span className="text-teal-600 dark:text-teal-400">Correct!</span>
                                        ) : (
                                            <span className="text-slate-600 dark:text-slate-400">Explanation:</span>
                                        )}
                                    </p>
                                    <p className="text-slate-600 dark:text-slate-300 text-sm">
                                        {content.questions[currentQuestionIdx].explanation}
                                    </p>
                                </div>

                                <button
                                    onClick={handleNextQuestion}
                                    className="w-full bg-cyan-600 text-white py-3 rounded-xl font-bold hover:bg-cyan-700 transition-all flex items-center justify-center gap-2"
                                >
                                    {currentQuestionIdx < content.questions.length - 1 ? 'Next Question' : 'Finish Lesson'}
                                    <ChevronRight size={20} />
                                </button>
                            </div>
                        )}

                        {!isAnswered && (
                            <button
                                onClick={handleSubmitAnswer}
                                disabled={selectedOption === null}
                                className="w-full mt-8 bg-slate-900 dark:bg-white dark:text-slate-900 text-white py-3 rounded-xl font-bold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                            >
                                Submit Answer
                            </button>
                        )}
                    </div>
                </div>
            )}

            {/* Completion View */}
            {mode === 'completed' && (
                <div className="text-center py-20 bg-white dark:bg-slate-800 rounded-3xl border border-slate-100 dark:border-slate-700 shadow-xl max-w-lg mx-auto animate-fade-in-up">
                    <div className="w-24 h-24 bg-teal-100 dark:bg-teal-900/20 rounded-full flex items-center justify-center text-teal-600 mx-auto mb-6 shadow-lg shadow-teal-500/20">
                        <CheckCircle2 size={48} />
                    </div>
                    <h2 className="text-3xl font-bold mb-2">Lesson Completed!</h2>
                    <p className="text-slate-500 dark:text-slate-400 mb-8">
                        You've mastered <span className="text-cyan-600 font-bold">{content.lesson_title}</span>.
                    </p>
                    <button
                        onClick={handleFinish}
                        className="w-full max-w-xs mx-auto bg-cyan-600 text-white py-4 rounded-xl font-bold hover:bg-cyan-700 transition-all shadow-lg shadow-cyan-500/30"
                    >
                        Continue Journey
                    </button>
                </div>
            )}
        </div>
    );
};

export default LessonView;
