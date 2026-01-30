import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Loader2, ArrowLeft, BookOpen, Clock, ChevronDown, ChevronRight, CheckCircle2, AlertCircle } from 'lucide-react';
import { API_BASE_URL } from '../api';

const RoadmapView = ({ topic, onBack }) => {
    const [roadmap, setRoadmap] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [expandedChapters, setExpandedChapters] = useState({});
    const [completedLessons, setCompletedLessons] = useState(() => {
        const saved = localStorage.getItem(`completed_${topic}`);
        return saved ? JSON.parse(saved) : {};
    });

    useEffect(() => {
        localStorage.setItem(`completed_${topic}`, JSON.stringify(completedLessons));
    }, [completedLessons, topic]);

    useEffect(() => {
        const fetchRoadmap = async () => {
            setLoading(true);
            try {
                const response = await axios.get(`${API_BASE_URL}/api/roadmaps/${topic}`);
                setRoadmap(response.data.roadmap);

                // Expand first chapter by default
                const chapters = Object.keys(response.data.roadmap);
                if (chapters.length > 0) {
                    setExpandedChapters({ [chapters[0]]: true });
                }
            } catch (err) {
                setError('Failed to load roadmap.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        if (topic) {
            fetchRoadmap();
        }
    }, [topic]);

    const toggleChapter = (chapter) => {
        setExpandedChapters(prev => ({
            ...prev,
            [chapter]: !prev[chapter]
        }));
    };

    const toggleLesson = (chapter, lesson) => {
        const key = `${chapter}-${lesson}`;
        setCompletedLessons(prev => ({
            ...prev,
            [key]: !prev[key]
        }));
    };

    const calculateChapterProgress = (chapter, lessons) => {
        const lessonKeys = Object.keys(lessons);
        if (lessonKeys.length === 0) return 0;
        const completedCount = lessonKeys.filter(l => completedLessons[`${chapter}-${l}`]).length;
        return (completedCount / lessonKeys.length) * 100;
    };

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-96 text-slate-400">
                <Loader2 className="w-10 h-10 animate-spin mb-4 text-cyan-500" />
                <p className="animate-pulse">Crafting your personalized path for {topic}...</p>
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

                <div className="relative z-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
                    <div>
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-300 text-xs font-bold uppercase tracking-wider mb-4 border border-cyan-500/30">
                            <BookOpen size={12} />
                            Active Learning Path
                        </div>
                        <h1 className="text-4xl md:text-5xl font-black mb-3 tracking-tight leading-tight">{topic}</h1>
                        <p className="text-slate-400 text-lg max-w-md">Your personalized curriculum is ready. Master each chapter at your own pace.</p>
                    </div>
                </div>
            </div>

            {/* Curriculum Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                <div className="bg-white dark:bg-slate-800 p-6 rounded-3xl border border-slate-100 dark:border-slate-700 shadow-sm">
                    <p className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">Chapters</p>
                    <p className="text-3xl font-bold dark:text-white">{Object.keys(roadmap).length}</p>
                </div>
                <div className="bg-white dark:bg-slate-800 p-6 rounded-3xl border border-slate-100 dark:border-slate-700 shadow-sm">
                    <p className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">Total Lessons</p>
                    <p className="text-3xl font-bold dark:text-white">
                        {Object.values(roadmap).reduce((acc, curr) => acc + Object.keys(curr).length, 0)}
                    </p>
                </div>
                <div className="bg-white dark:bg-slate-800 p-6 rounded-3xl border border-slate-100 dark:border-slate-700 shadow-sm">
                    <p className="text-slate-500 dark:text-slate-400 text-sm font-medium mb-1">Progress</p>
                    <p className="text-3xl font-bold text-cyan-600">
                        {Math.round((Object.keys(completedLessons).length / Math.max(1, Object.values(roadmap).reduce((acc, curr) => acc + Object.keys(curr).length, 0))) * 100)}%
                    </p>
                </div>
            </div>

            {/* Chapters List */}
            <div className="space-y-4">
                {Object.entries(roadmap).map(([chapterTitle, lessons], idx) => {
                    const progress = calculateChapterProgress(chapterTitle, lessons);
                    const isExpanded = expandedChapters[chapterTitle];

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
                                        <div className="flex items-center gap-3 mt-1">
                                            <div className="w-24 h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-cyan-500 transition-all duration-1000 ease-out"
                                                    style={{ width: `${progress}%` }}
                                                />
                                            </div>
                                            <span className="text-xs font-semibold text-slate-400">{Math.round(progress)}% Complete</span>
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
                                        const lessonKey = `${chapterTitle}-${lessonTitle}`;
                                        const isCompleted = completedLessons[lessonKey];

                                        return (
                                            <div
                                                key={lIdx}
                                                onClick={() => toggleLesson(chapterTitle, lessonTitle)}
                                                className={`group p-5 rounded-2xl border transition-all duration-200 cursor-pointer flex gap-4 items-start ${isCompleted
                                                    ? 'bg-teal-50/30 dark:bg-teal-900/10 border-teal-100 dark:border-teal-900/30 shadow-inner'
                                                    : 'bg-white dark:bg-slate-700/30 border-slate-100 dark:border-slate-700 hover:border-cyan-200 dark:hover:border-cyan-800'
                                                    }`}
                                            >
                                                <div className={`mt-0.5 w-6 h-6 rounded-full flex items-center justify-center border-2 transition-all ${isCompleted
                                                    ? 'bg-teal-500 border-teal-500 text-white'
                                                    : 'border-slate-200 dark:border-slate-600 text-transparent group-hover:border-cyan-400'
                                                    }`}>
                                                    <CheckCircle2 size={14} />
                                                </div>
                                                <div className="flex-1">
                                                    <h4 className={`font-bold transition-colors ${isCompleted ? 'text-teal-700 dark:text-teal-400' : 'text-slate-800 dark:text-white'}`}>
                                                        {lessonTitle}
                                                    </h4>
                                                    <p className={`text-sm leading-relaxed mt-1 transition-colors ${isCompleted ? 'text-teal-600/70 dark:text-teal-400/50' : 'text-slate-500 dark:text-slate-400'}`}>
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
