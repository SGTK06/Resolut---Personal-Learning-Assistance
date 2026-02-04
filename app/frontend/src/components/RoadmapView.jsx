import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Loader2, ArrowLeft, BookOpen, Clock, ChevronDown, ChevronRight, CheckCircle2, Lock, PlayCircle, AlertCircle, Calendar } from 'lucide-react';
import { API_BASE_URL } from '../api';
import SchedulingModal from './SchedulingModal';

const RoadmapView = ({ topic, onBack, onLessonSelect, isCalendarConnected = false }) => {
    const [roadmap, setRoadmap] = useState(null);
    const [progress, setProgress] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [expandedChapters, setExpandedChapters] = useState({});
    const [isSchedulingOpen, setIsSchedulingOpen] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                // Parallel fetch: Roadmap + Progress
                const [roadmapRes, progressRes] = await Promise.all([
                    axios.get(`${API_BASE_URL}/api/roadmaps/${encodeURIComponent(topic)}`),
                    axios.get(`${API_BASE_URL}/api/lessons/progress/${encodeURIComponent(topic)}`)
                ]);

                setRoadmap(roadmapRes.data.roadmap);
                setProgress(progressRes.data);

                // Default expand the current chapter or the first one
                const chapters = Object.keys(roadmapRes.data.roadmap);
                const currentChap = progressRes.data?.current_chapter;

                if (currentChap && chapters.includes(currentChap)) {
                    setExpandedChapters({ [currentChap]: true });
                } else if (chapters.length > 0) {
                    setExpandedChapters({ [chapters[0]]: true });
                }

            } catch (err) {
                setError('Failed to load learning path.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        if (topic) {
            fetchData();
        }
    }, [topic]);

    const toggleChapter = (chapter) => {
        setExpandedChapters(prev => ({
            ...prev,
            [chapter]: !prev[chapter]
        }));
    };

    const isLessonCompleted = (chapter, lesson) => {
        if (!progress || !progress.completed_lessons) return false;
        const id = `${chapter}: ${lesson}`;
        return progress.completed_lessons.includes(id);
    };

    const isLessonUnlocked = (chapter, lesson) => {
        // 1. If completed, it's unlocked
        if (isLessonCompleted(chapter, lesson)) return true;

        // 2. If it is the EXACT current target (chapter & lesson match progress)
        if (progress && progress.current_chapter === chapter && progress.current_lesson === lesson) {
            return true;
        }

        // 3. Fallback: If no progress exists yet (new topic), unlock ONLY the very first lesson of first chapter
        if (progress && progress.status === 'not_started' && roadmap) {
            const firstChapter = Object.keys(roadmap)[0];
            if (chapter === firstChapter) {
                const firstLesson = Object.keys(roadmap[firstChapter])[0];
                return lesson === firstLesson;
            }
        }

        return false;
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-96 text-slate-400">
                <Loader2 className="w-10 h-10 animate-spin mb-4 text-cyan-500" />
                <p className="animate-pulse">Loading your progress...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="text-center p-12 bg-white dark:bg-slate-800 rounded-3xl border border-red-100 dark:border-red-900/20 shadow-xl max-w-lg mx-auto">
                <div className="w-16 h-16 bg-red-50 dark:bg-red-900/30 rounded-full flex items-center justify-center text-red-600 mx-auto mb-4">
                    <AlertCircle size={32} />
                </div>
                <h3 className="text-xl font-bold dark:text-white mb-2">Oops!</h3>
                <p className="text-slate-500 dark:text-slate-400 mb-6">{error}</p>
                <button onClick={onBack} className="bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200 px-6 py-2 rounded-xl font-bold hover:bg-slate-200 transition-all">
                    Go Back to Dashboard
                </button>
            </div>
        );
    }

    if (!roadmap || Object.keys(roadmap).length === 0) {
        return (
            <div className="text-center p-12 bg-white dark:bg-slate-800 rounded-3xl border border-slate-100 dark:border-slate-700 shadow-xl max-w-lg mx-auto">
                <div className="w-16 h-16 bg-slate-50 dark:bg-slate-700 rounded-full flex items-center justify-center text-slate-400 mx-auto mb-4">
                    <BookOpen size={32} />
                </div>
                <h3 className="text-xl font-bold dark:text-white mb-2">No Roadmap Yet</h3>
                <p className="text-slate-500 dark:text-slate-400 mb-6">We couldn't find a learning path for this topic.</p>
                <button onClick={onBack} className="text-cyan-600 font-bold hover:text-cyan-700">
                    &larr; Return to Dashboard
                </button>
            </div>
        );
    }

    // Calculate overall progress
    const totalLessons = Object.values(roadmap).reduce((acc, curr) => acc + Object.keys(curr).length, 0);
    const completedCount = progress?.completed_lessons?.length || 0;
    const progressPercent = Math.round((completedCount / Math.max(1, totalLessons)) * 100);

    return (
        <div className="max-w-4xl mx-auto space-y-6 animate-fade-in pb-20">
            {/* Header Area */}
            <div className="flex items-center justify-between mb-4">
                <button
                    onClick={onBack}
                    className="flex items-center gap-2 text-slate-500 hover:text-cyan-600 transition-colors group px-4 py-2 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                    <ArrowLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
                    <span className="font-medium">Dashboard</span>
                </button>
            </div>

            <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-cyan-900 rounded-[2.5rem] p-10 text-white shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>
                <div className="absolute bottom-0 left-0 w-32 h-32 bg-teal-500/10 rounded-full blur-2xl -ml-8 -mb-8 pointer-events-none"></div>

                <div className="relative z-10">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-300 text-xs font-bold uppercase tracking-wider border border-cyan-500/30">
                            <BookOpen size={12} />
                            Active Learning Path
                        </div>
                        {isCalendarConnected && (
                            <button
                                onClick={() => setIsSchedulingOpen(true)}
                                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white text-sm font-bold border border-white/20 transition-all backdrop-blur-sm shadow-lg shadow-white/5 active:scale-95"
                            >
                                <Calendar size={16} className="text-cyan-400" />
                                Schedule Study Session
                            </button>
                        )}
                    </div>
                    <h1 className="text-4xl md:text-5xl font-black mb-3 tracking-tight leading-tight">{topic}</h1>
                    <div className="flex items-center gap-4 mt-6">
                        <div className="flex-1 bg-white/10 rounded-full h-2 overflow-hidden backdrop-blur-sm">
                            <div className="bg-cyan-400 h-full rounded-full transition-all duration-1000" style={{ width: `${progressPercent}%` }}></div>
                        </div>
                        <span className="font-bold">{progressPercent}% Mastered</span>
                    </div>
                </div>
            </div>

            <SchedulingModal
                isOpen={isSchedulingOpen}
                onClose={() => setIsSchedulingOpen(false)}
                topic={topic}
            />

            {/* Chapters List */}
            <div className="space-y-4">
                {Object.entries(roadmap).map(([chapterTitle, lessons], idx) => {
                    const isExpanded = expandedChapters[chapterTitle];
                    const lessonKeys = Object.keys(lessons);

                    // Chapter progress
                    const chapterCompleted = lessonKeys.filter(l => isLessonCompleted(chapterTitle, l)).length;
                    const chapterProgress = (chapterCompleted / Math.max(1, lessonKeys.length)) * 100;

                    return (
                        <div
                            key={idx}
                            className={`bg-white dark:bg-slate-800 rounded-[2rem] border transition-all duration-300 overflow-hidden shadow-sm hover:shadow-md ${isExpanded ? 'border-cyan-200 dark:border-cyan-900/50 ring-1 ring-cyan-100 dark:ring-cyan-900/20' : 'border-slate-200 dark:border-slate-700'
                                }`}
                        >
                            {/* Chapter Header */}
                            <div
                                onClick={() => toggleChapter(chapterTitle)}
                                className="p-6 cursor-pointer flex items-center justify-between"
                            >
                                <div className="flex items-center gap-5">
                                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center font-bold text-xl transition-all duration-300 ${isExpanded
                                        ? 'bg-cyan-600 text-white rotate-3 shadow-lg shadow-cyan-500/20'
                                        : 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-400'
                                        }`}>
                                        {idx + 1}
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-bold dark:text-white leading-tight">{chapterTitle}</h3>
                                        <div className="flex items-center gap-2 mt-1 text-sm text-slate-400">
                                            <span>{Math.round(chapterProgress)}% Complete</span>
                                        </div>
                                    </div>
                                </div>
                                <div className={`text-slate-400 p-2 rounded-full transition-colors ${isExpanded ? 'bg-cyan-50 dark:bg-cyan-900/20 text-cyan-600' : ''}`}>
                                    {isExpanded ? <ChevronDown size={24} /> : <ChevronRight size={24} />}
                                </div>
                            </div>

                            {/* Lessons Content */}
                            {isExpanded && (
                                <div className="px-6 pb-8 pt-0 space-y-3 animate-slide-down">
                                    {Object.entries(lessons).map(([lessonTitle, lessonDesc], lIdx) => {
                                        const unlocked = isLessonUnlocked(chapterTitle, lessonTitle);
                                        const completed = isLessonCompleted(chapterTitle, lessonTitle);

                                        return (
                                            <div
                                                key={lIdx}
                                                onClick={() => unlocked && onLessonSelect(chapterTitle, lessonTitle)}
                                                className={`group p-5 rounded-2xl border transition-all duration-200 flex gap-4 items-start ${unlocked
                                                    ? 'cursor-pointer hover:border-cyan-200 dark:hover:border-cyan-800 bg-white dark:bg-slate-700/30'
                                                    : 'cursor-not-allowed opacity-60 bg-slate-50 dark:bg-slate-800/50 grayscale'
                                                    } ${completed
                                                        ? 'bg-teal-50/30 dark:bg-teal-900/10 border-teal-100 dark:border-teal-900/30 shadow-inner'
                                                        : 'border-slate-100 dark:border-slate-700'
                                                    }`}
                                            >
                                                <div className={`mt-0.5 w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all shrink-0 ${completed
                                                    ? 'bg-teal-500 border-teal-500 text-white'
                                                    : unlocked
                                                        ? 'border-cyan-500 text-cyan-500 bg-cyan-50 dark:bg-cyan-900/20'
                                                        : 'border-slate-300 text-slate-300 dark:border-slate-600 dark:text-slate-600'
                                                    }`}>
                                                    {completed ? <CheckCircle2 size={16} /> : unlocked ? <PlayCircle size={16} /> : <Lock size={16} />}
                                                </div>
                                                <div className="flex-1">
                                                    <h4 className={`font-bold transition-colors ${completed ? 'text-teal-700 dark:text-teal-400' :
                                                        unlocked ? 'text-slate-900 dark:text-white group-hover:text-cyan-600' : 'text-slate-400 dark:text-slate-500'
                                                        }`}>
                                                        {lessonTitle}
                                                    </h4>
                                                    <p className={`text-sm leading-relaxed mt-1 transition-colors ${completed ? 'text-teal-600/70 dark:text-teal-400/50' : 'text-slate-500 dark:text-slate-400'
                                                        }`}>
                                                        {lessonDesc}
                                                    </p>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default RoadmapView;
