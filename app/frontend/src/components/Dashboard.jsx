import React, { useState, useEffect } from 'react';
import {
    Moon,
    Sun,
    PlusCircle,
    LogOut,
    LayoutDashboard
} from 'lucide-react';
import LearnTopicFlow from './LearnTopicFlow';

const Dashboard = () => {
    const [isDarkMode, setIsDarkMode] = useState(
        window.matchMedia('(prefers-color-scheme: dark)').matches
    );
    const [showLearningFlow, setShowLearningFlow] = useState(false);

    useEffect(() => {
        const root = window.document.documentElement;
        if (isDarkMode) {
            root.setAttribute('data-theme', 'dark');
        } else {
            root.removeAttribute('data-theme');
        }
    }, [isDarkMode]);

    const toggleDarkMode = () => setIsDarkMode(!isDarkMode);

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-300 flex flex-col">
            {/* Header */}
            <header className="h-20 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-8 flex items-center justify-between sticky top-0 z-10">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-cyan-500 rounded-lg flex items-center justify-center shadow-lg shadow-cyan-500/30">
                        <span className="text-white font-bold text-xl">R</span>
                    </div>
                    <span className="text-xl font-bold dark:text-white">Resolut</span>
                </div>

                <div className="flex items-center gap-4">
                    <button
                        onClick={toggleDarkMode}
                        className="p-2 text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-all"
                    >
                        {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
                    </button>
                    <div className="w-10 h-10 bg-slate-200 dark:bg-slate-700 rounded-full border-2 border-white dark:border-slate-600 overflow-hidden">
                        <img src="https://ui-avatars.com/api/?name=User" alt="User Avatar" />
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="flex-1 max-w-5xl w-full mx-auto p-6 md:p-8">
                {!showLearningFlow ? (
                    <div className="space-y-8 animate-fade-in-up">
                        <div className="bg-gradient-to-br from-cyan-500 to-teal-600 rounded-3xl p-8 text-white shadow-xl shadow-cyan-500/20 relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>

                            <h2 className="text-4xl font-bold mb-3 relative z-10">Welcome Back!</h2>
                            <p className="opacity-90 text-lg mb-8 max-w-xl relative z-10">Ready to master a new skill today? Your journey to knowledge starts here.</p>

                            <button
                                onClick={() => setShowLearningFlow(true)}
                                className="bg-white text-cyan-600 px-8 py-4 rounded-xl font-bold flex items-center gap-2 hover:bg-slate-50 hover:scale-105 transition-all shadow-lg"
                            >
                                <PlusCircle size={22} />
                                Start Learning a New Topic
                            </button>
                        </div>

                        <div>
                            <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-6 flex items-center gap-2">
                                <LayoutDashboard className="text-cyan-500" size={24} />
                                Dashboard Overview
                            </h3>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 hover:border-cyan-200 dark:hover:border-cyan-800 transition-colors group">
                                    <h3 className="text-slate-500 dark:text-slate-400 font-medium mb-1 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 transition-colors">Topics In Progress</h3>
                                    <p className="text-4xl font-bold dark:text-white">0</p>
                                </div>
                                <div className="bg-white dark:bg-slate-800 p-6 rounded-2xl shadow-sm border border-slate-100 dark:border-slate-700 hover:border-cyan-200 dark:hover:border-cyan-800 transition-colors group">
                                    <h3 className="text-slate-500 dark:text-slate-400 font-medium mb-1 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 transition-colors">Total Hours</h3>
                                    <p className="text-4xl font-bold dark:text-white">0</p>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="animate-fade-in-up">
                        <button
                            onClick={() => setShowLearningFlow(false)}
                            className="mb-6 text-slate-500 dark:text-slate-400 hover:text-cyan-600 dark:hover:text-cyan-400 flex items-center gap-2 transition-colors font-medium"
                        >
                            ← Back to Dashboard
                        </button>
                        <LearnTopicFlow onCancel={() => setShowLearningFlow(false)} />
                    </div>
                )}
            </main>
        </div>
    );
};

export default Dashboard;
