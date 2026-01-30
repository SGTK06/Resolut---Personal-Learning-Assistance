import React, { useState, useEffect } from 'react';
import {
    Moon,
    Sun,
    PlusCircle,
    LogOut,
    LayoutDashboard
} from 'lucide-react';
import LearnTopicFlow from './LearnTopicFlow';
import TopicDashboard from './TopicDashboard';
import RoadmapView from './RoadmapView';

const Dashboard = () => {
    const [isDarkMode, setIsDarkMode] = useState(
        window.matchMedia('(prefers-color-scheme: dark)').matches
    );

    // Views: 'dashboard' | 'create' | 'roadmap'
    const [view, setView] = useState('dashboard');
    const [activeTopic, setActiveTopic] = useState(null);

    useEffect(() => {
        const root = window.document.documentElement;
        if (isDarkMode) {
            root.setAttribute('data-theme', 'dark');
        } else {
            root.removeAttribute('data-theme');
        }
    }, [isDarkMode]);

    const toggleDarkMode = () => setIsDarkMode(!isDarkMode);

    const handleNewTopic = () => setView('create');

    const handleViewRoadmap = (topic) => {
        setActiveTopic(topic);
        setView('roadmap');
    };

    const handleBackToDashboard = () => {
        setActiveTopic(null);
        setView('dashboard');
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-300 flex flex-col">
            {/* Header */}
            <header className="h-20 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-8 flex items-center justify-between sticky top-0 z-10 shadow-sm">
                <div
                    className="flex items-center gap-3 cursor-pointer"
                    onClick={handleBackToDashboard}
                >
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
            <main className="flex-1 max-w-6xl w-full mx-auto p-6 md:p-8">
                {view === 'dashboard' && (
                    <TopicDashboard
                        onNewTopic={handleNewTopic}
                        onViewRoadmap={handleViewRoadmap}
                    />
                )}

                {view === 'create' && (
                    <div className="animate-fade-in-up">
                        <button
                            onClick={handleBackToDashboard}
                            className="mb-6 text-slate-500 dark:text-slate-400 hover:text-cyan-600 dark:hover:text-cyan-400 flex items-center gap-2 transition-colors font-medium"
                        >
                            ← Back to Dashboard
                        </button>
                        <LearnTopicFlow
                            onCancel={handleBackToDashboard}
                        />
                    </div>
                )}

                {view === 'roadmap' && activeTopic && (
                    <RoadmapView
                        topic={activeTopic}
                        onBack={handleBackToDashboard}
                    />
                )}
            </main>
        </div>
    );
};

export default Dashboard;
