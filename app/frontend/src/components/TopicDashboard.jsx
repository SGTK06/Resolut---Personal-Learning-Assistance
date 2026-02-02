import React, { useState, useEffect } from 'react';
import {
    Trash2,
    Plus,
    BookOpen,
    Loader2,
    AlertCircle,
    Calendar,
    Clock,
    ChevronRight,
    Search
} from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../api';

const TopicDashboard = ({ onNewTopic, onViewRoadmap }) => {
    const [topics, setTopics] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [deleteLoading, setDeleteLoading] = useState(null);

    const fetchTopics = async (retryCount = 0) => {
        setLoading(true);
        setError(null);
        try {
            const response = await axios.get(`${API_BASE_URL}/api/topics`);
            const list = response.data?.topics;
            setTopics(Array.isArray(list) ? list : []);
            setError(null);
        } catch (err) {
            const isBackendDown = err.code === 'ERR_NETWORK' || err.message?.includes('Network Error') || (err.response?.status && [500, 502, 503].includes(err.response.status));

            // Auto-retry if backend seems down during startup (up to 5 times)
            if (isBackendDown && retryCount < 5) {
                console.log(`Backend not ready, retrying... (${retryCount + 1}/5)`);
                setTimeout(() => fetchTopics(retryCount + 1), 2000);
                return;
            }

            setError(
                isBackendDown
                    ? 'Backend not running. In another terminal, from the app folder run: npm run backend — then click Retry.'
                    : 'Failed to load topics. If the backend is not running, start it with: npm run backend'
            );
            setTopics([]);
            console.error(err);
        } finally {
            if (retryCount === 0 || !loading) {
                setLoading(false);
            }
        }
    };

    useEffect(() => {
        fetchTopics();
    }, []);

    const handleDelete = async (topic, e) => {
        e.stopPropagation();
        if (!window.confirm(`Are you sure you want to delete "${topic}"?\nThis will remove all associated files and roadmap data from your device.`)) {
            return;
        }

        setDeleteLoading(topic);
        try {
            await axios.delete(`${API_BASE_URL}/api/topics/${encodeURIComponent(topic)}`);
            setTopics(topics.filter(t => t !== topic));
        } catch (err) {
            alert('Failed to delete topic: ' + err.message);
        } finally {
            setDeleteLoading(null);
        }
    };

    const filteredTopics = topics.filter(t =>
        t.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading && topics.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-12 text-slate-400">
                <Loader2 className="w-8 h-8 animate-spin mb-4" />
                <p>Loading your learning paths...</p>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-fade-in">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold dark:text-white">Your Learning Paths</h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-1">Manage your topics and track progress</p>
                </div>
                <button
                    onClick={onNewTopic}
                    className="bg-cyan-600 text-white px-6 py-3 rounded-xl font-bold hover:bg-cyan-700 flex items-center gap-2 transition-all shadow-lg shadow-cyan-500/20"
                >
                    <Plus size={20} />
                    New Topic
                </button>
            </div>

            {/* Error Banner */}
            {error && (
                <div className="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-4 rounded-xl flex items-center justify-between gap-4 border border-red-200 dark:border-red-800">
                    <div className="flex items-center gap-2">
                        <AlertCircle size={20} className="flex-shrink-0" />
                        <span>{error}</span>
                    </div>
                    <button
                        onClick={() => fetchTopics()}
                        className="px-4 py-2 bg-red-100 dark:bg-red-900/40 hover:bg-red-200 dark:hover:bg-red-900/60 rounded-lg font-medium transition-colors flex-shrink-0"
                    >
                        Retry
                    </button>
                </div>
            )}

            {/* Search & Grid */}
            <div className="space-y-4">
                {topics.length > 0 && (
                    <div className="relative max-w-md">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={20} />
                        <input
                            type="text"
                            placeholder="Search topics..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl outline-none focus:ring-2 focus:ring-cyan-500 transition-all dark:text-white"
                        />
                    </div>
                )}

                {topics.length === 0 ? (
                    <div className="text-center py-20 bg-slate-50 dark:bg-slate-800/50 rounded-3xl border border-dashed border-slate-200 dark:border-slate-700">
                        <div className="w-16 h-16 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center mx-auto mb-4 text-slate-400">
                            <BookOpen size={32} />
                        </div>
                        <h3 className="text-xl font-bold dark:text-white mb-2">No topics yet</h3>
                        <p className="text-slate-500 dark:text-slate-400 mb-6 max-w-sm mx-auto">
                            Start your learning journey by creating your first topic.
                        </p>
                        <button
                            onClick={onNewTopic}
                            className="text-cyan-600 font-bold hover:text-cyan-700"
                        >
                            Create Topic &rarr;
                        </button>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {filteredTopics.map((topic) => (
                            <div
                                key={topic}
                                onClick={() => onViewRoadmap(topic)}
                                className="group bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 hover:border-cyan-500 dark:hover:border-cyan-500 hover:shadow-xl hover:shadow-cyan-500/10 transition-all cursor-pointer relative overflow-hidden"
                            >
                                <div className="absolute top-0 right-0 p-4 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                        onClick={(e) => handleDelete(topic, e)}
                                        disabled={deleteLoading === topic}
                                        className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-all"
                                        title="Delete Topic"
                                    >
                                        {deleteLoading === topic ? <Loader2 className="animate-spin" size={18} /> : <Trash2 size={18} />}
                                    </button>
                                </div>

                                <div className="w-12 h-12 bg-cyan-100 dark:bg-cyan-900/30 rounded-xl flex items-center justify-center text-cyan-600 mb-4 group-hover:scale-110 transition-transform">
                                    <BookOpen size={24} />
                                </div>

                                <h3 className="text-xl font-bold dark:text-white mb-2 truncate pr-8">{topic}</h3>

                                <div className="flex items-center gap-4 text-sm text-slate-500 dark:text-slate-400 mt-4">
                                    <span className="flex items-center gap-1">
                                        <Calendar size={14} />
                                        <span>Plan Ready</span>
                                    </span>
                                    <span className="flex items-center gap-1 text-cyan-600 font-medium group-hover:translate-x-1 transition-transform ml-auto">
                                        View Roadmap
                                        <ChevronRight size={14} />
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default TopicDashboard;
