import React, { useState, useEffect } from 'react';
import {
    Moon,
    Sun,
    PlusCircle,
    LogOut,
    LayoutDashboard,
    BookOpen,
    Settings,
    Calendar,
    CheckCircle2,
    AlertCircle,
    Loader2
} from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../api';
import LearnTopicFlow from './LearnTopicFlow';
import TopicDashboard from './TopicDashboard';
import RoadmapView from './RoadmapView';
import LessonView from './LessonView';
import SchedulingModal from './SchedulingModal';
import logo from '../assets/logo.png';
const Dashboard = () => {
    const [isDarkMode, setIsDarkMode] = useState(
        window.matchMedia('(prefers-color-scheme: dark)').matches
    );

    // Views: 'dashboard' | 'create' | 'roadmap' | 'lesson'
    const [view, setView] = useState('dashboard');
    const [activeTopic, setActiveTopic] = useState(null);
    const [currentLesson, setCurrentLesson] = useState(null);
    const [calendarConnected, setCalendarConnected] = useState(false);
    const [hasCredentials, setHasCredentials] = useState(false);
    const [calendarLoading, setCalendarLoading] = useState(false);
    const [isGeneralSchedulingOpen, setIsGeneralSchedulingOpen] = useState(false);

    useEffect(() => {
        const checkStatus = async () => {
            // Check connectivity
            try {
                const statusRes = await axios.get(`${API_BASE_URL}/api/calendar/status`);
                setCalendarConnected(statusRes.data.connected);
                if (statusRes.data.error) {
                    console.warn("Calendar status error:", statusRes.data.error);
                }
            } catch (err) {
                console.error("Failed to check calendar connectivity", err);
            }

            // Check config
            try {
                const configRes = await axios.get(`${API_BASE_URL}/api/calendar/config-status`);
                setHasCredentials(configRes.data.has_credentials);
                if (configRes.data.error) {
                    console.warn("Calendar config error:", configRes.data.error);
                }
            } catch (err) {
                console.error("Failed to check calendar config", err);
            }
        };
        checkStatus();
    }, []);

    const handleConnectCalendar = async () => {
        if (calendarConnected) {
            setIsGeneralSchedulingOpen(true);
            return;
        }

        if (!hasCredentials) {
            // Try to fetch detailed status to show a better error
            try {
                const configRes = await axios.get(`${API_BASE_URL}/api/calendar/config-status`);
                const details = configRes.data;
                const pathMsg = details.checked_path ? `\nChecked path: ${details.checked_path}` : "";
                const envMsg = details.has_env === false ? "\nEnvironment variables not detected." : "";
                const fileMsg = details.has_file === false ? "\nCredentials file not found." : "";

                alert(`Google Calendar is not configured.\n${envMsg}${fileMsg}${pathMsg}\n\nPlease check README.md for developer setup instructions.`);
            } catch (err) {
                alert("Google Calendar is not configured. Please check README.md for developer setup instructions.");
            }
            return;
        }

        setCalendarLoading(true);
        try {
            await axios.get(`${API_BASE_URL}/api/calendar/connect`);
            setCalendarConnected(true);
        } catch (err) {
            console.error("Failed to connect calendar:", err);
            alert("Connection failed. Ensure the Google Calendar API is enabled and your credentials are valid.");
        } finally {
            setCalendarLoading(false);
        }
    };

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
        setCurrentLesson(null);
        setView('dashboard');
    };

    const handleBackToRoadmap = () => {
        setCurrentLesson(null);
        setView('roadmap');
    };

    const handleStartLesson = (chapter, lesson) => {
        setCurrentLesson({
            topic: activeTopic,
            chapter,
            lesson
        });
        setView('lesson');
    };

    const handleLessonComplete = async () => {
        if (!currentLesson) return;

        // 1. Find the next lesson (simple logic: current lesson + 1, or next chapter)
        // ideally backend calculates this, but for now we essentially assume the backend updates progress.
        // We need to call the "complete" endpoint.

        // However, looking at the backend API, completion takes { topic, current_chapter, current_lesson, next_chapter, next_lesson }
        // The backend `update_progress` relies on US telling it what the next one is.
        // This means we need the Roadmap structure to know what comes next.
        // For simplicity in this iteration, we will just mark the CURRENT one as done.
        // ACTUALLY, the spec says "Unlock next lesson".
        // Let's rely on the backend to be smart, OR we calculate 'next' here if we had the roadmap.
        // Since we don't have the roadmap handy in Dashboard easily without fetching it again,
        // we might need to fetch the roadmap OR pass it up from LessonView?
        //
        // Better approach for now:
        // Just call a simplified completion endpoint if possible.
        // But since we built `POST /api/lessons/complete` expecting `next_chapter` etc...
        // We will fetch the roadmap briefly here or rely on the fact that when we go back to RoadmapView, it fetches progress.
        // ALL WE NEED TO DO is send the payload.
        //
        // WAIT: The backend `complete_lesson` function updates `completed_lessons` list with the `current` one.
        // It updates `current_chapter` and `current_lesson` to the `next` arguments.
        // So we DO need to know what's next.

        try {
            // Fetch roadmap to determine next lesson
            const roadmapRes = await axios.get(`${API_BASE_URL}/api/roadmaps/${encodeURIComponent(activeTopic)}`);
            const roadmapResult = roadmapRes.data.roadmap;

            let nextChapter = currentLesson.chapter;
            let nextLessonTitle = currentLesson.lesson;

            // Find current position
            const chapters = Object.keys(roadmapResult);
            const currentChapIdx = chapters.indexOf(currentLesson.chapter);

            if (currentChapIdx !== -1) {
                const lessons = Object.keys(roadmapResult[currentLesson.chapter]);
                const currentLessonIdx = lessons.indexOf(currentLesson.lesson);

                if (currentLessonIdx < lessons.length - 1) {
                    // Next lesson in same chapter
                    nextLessonTitle = lessons[currentLessonIdx + 1];
                } else if (currentChapIdx < chapters.length - 1) {
                    // Next chapter
                    nextChapter = chapters[currentChapIdx + 1];
                    const nextChapLessons = Object.keys(roadmapResult[nextChapter]);
                    nextLessonTitle = nextChapLessons[0];
                } else {
                    // Course completed? Keep as is or mark finished?
                    // For now, just keep at last lesson
                }
            }

            await axios.post(`${API_BASE_URL}/api/lessons/complete`, {
                topic: activeTopic,
                current_chapter: currentLesson.chapter,
                current_lesson: currentLesson.lesson,
                next_chapter: nextChapter,
                next_lesson: nextLessonTitle
            });

            // Return to roadmap
            handleBackToRoadmap();

        } catch (err) {
            console.error("Failed to mark lesson complete", err);
            alert("Failed to save progress. Please try again.");
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 transition-colors duration-300 flex flex-col">
            {/* Header */}
            <header className="h-20 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 px-8 flex items-center justify-between sticky top-0 z-10 shadow-sm">
                <div
                    className="flex items-center gap-3 cursor-pointer"
                    onClick={handleBackToDashboard}
                >
                    <div className="w-10 h-10  flex items-center justify-center">
                        <img src={logo} alt="Resolut Logo" className="w-full h-full object-contain" />
                    </div>
                    <span className="text-xl font-bold dark:text-white">Resolut</span>
                </div>

                <div className="flex items-center gap-4">
                    <button
                        onClick={handleConnectCalendar}
                        disabled={calendarLoading}
                        className={`p-2 rounded-lg transition-all flex items-center gap-2 ${calendarConnected
                            ? 'text-cyan-600 bg-cyan-50 dark:bg-cyan-900/20 border border-cyan-200 dark:border-cyan-800'
                            : hasCredentials
                                ? 'text-amber-600 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800'
                                : 'text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'
                            }`}
                        title={calendarConnected ? "Calendar Connected" : hasCredentials ? "Credentials Found - Click to Connect" : "Connect Google Calendar"}
                    >
                        {calendarLoading ? (
                            <Loader2 size={20} className="animate-spin" />
                        ) : calendarConnected ? (
                            <Calendar size={20} />
                        ) : hasCredentials ? (
                            <Calendar size={20} className="text-amber-500" />
                        ) : (
                            <Calendar size={20} className="opacity-50" />
                        )}
                        {calendarConnected && <span className="text-xs font-bold uppercase tracking-wider">Connected</span>}
                        {!calendarConnected && hasCredentials && <span className="text-[10px] font-bold uppercase tracking-wider text-amber-600">Configured</span>}
                    </button>

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
                        onLessonSelect={handleStartLesson}
                        isCalendarConnected={calendarConnected}
                    />
                )}

                {view === 'lesson' && currentLesson && (
                    <LessonView
                        topic={activeTopic}
                        chapter={currentLesson.chapter}
                        lesson={currentLesson.lesson}
                        onBack={handleBackToRoadmap}
                        onComplete={handleLessonComplete}
                    />
                )}
            </main>

            <SchedulingModal
                isOpen={isGeneralSchedulingOpen}
                onClose={() => setIsGeneralSchedulingOpen(false)}
                topic="General Learning"
            />
        </div>
    );
};

export default Dashboard;
