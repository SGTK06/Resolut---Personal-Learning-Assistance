import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, Loader2, Calendar, Layout, History, CheckCircle2 } from 'lucide-react';
import { API_BASE_URL } from '../api';

const SchedulingModal = ({ isOpen, onClose }) => {
    const [sessions, setSessions] = useState([]);
    const [fetchingSessions, setFetchingSessions] = useState(false);

    useEffect(() => {
        if (isOpen) {
            fetchSessions();
        }
    }, [isOpen]);


    const fetchSessions = async () => {
        setFetchingSessions(true);
        try {
            const response = await axios.get(`${API_BASE_URL}/api/calendar/sessions`);
            if (response.data.status === 'success') {
                setSessions(response.data.sessions);
            }
        } catch (err) {
            console.error("Failed to fetch sessions:", err);
        } finally {
            setFetchingSessions(false);
        }
    };

    const formatTime = (iso) => {
        return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });
    };

    const formatDate = (iso) => {
        const d = new Date(iso);
        const today = new Date();
        if (d.toDateString() === today.toDateString()) return 'Today';
        return d.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in text-slate-800 dark:text-slate-100">
            <div className="bg-white dark:bg-slate-800 w-full max-w-lg rounded-[2.5rem] shadow-2xl border border-slate-200 dark:border-slate-700 flex flex-col overflow-hidden animate-slide-up">
                {/* Header */}
                <div className="p-6 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between bg-gradient-to-r from-cyan-50 to-transparent dark:from-cyan-900/10">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-cyan-600 rounded-xl flex items-center justify-center text-white shadow-lg shadow-cyan-500/30">
                            <Calendar size={20} />
                        </div>
                        <div>
                            <h3 className="font-bold text-lg">My Learning Schedule</h3>
                            <p className="text-xs text-slate-500">Autonomous learning organizer</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-full transition-colors text-slate-400">
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-8 space-y-6 bg-slate-50/50 dark:bg-slate-900/30">
                    {/* Status Info */}
                    <div className="bg-cyan-50 dark:bg-cyan-900/20 p-4 rounded-3xl border border-cyan-100 dark:border-cyan-800/50">
                        <p className="text-xs text-cyan-800 dark:text-cyan-300 leading-relaxed font-medium">
                            Resolut automatically scans your calendar and books a 1-hour study session every day upon startup to keep you on track.
                        </p>
                    </div>

                    {/* Upcoming Sessions List */}
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                <Layout size={14} />
                                Upcoming Sessions (24h)
                            </h4>
                            {fetchingSessions && <Loader2 size={12} className="animate-spin text-cyan-500" />}
                        </div>

                        <div className="space-y-3">
                            {sessions.length === 0 ? (
                                <div className="p-10 text-center bg-white dark:bg-slate-800 rounded-[2rem] border border-dashed border-slate-200 dark:border-slate-700">
                                    <div className="w-12 h-12 bg-slate-50 dark:bg-slate-900 rounded-full flex items-center justify-center mx-auto mb-3 text-slate-300">
                                        <Calendar size={24} />
                                    </div>
                                    <p className="text-xs text-slate-500">No study sessions found for the next 24 hours.</p>
                                </div>
                            ) : (
                                sessions.map((session, idx) => (
                                    <div key={idx} className="p-4 bg-white dark:bg-slate-800 rounded-3xl border border-slate-100 dark:border-slate-700 shadow-sm flex items-center justify-between">
                                        <div className="flex gap-4 items-center">
                                            <div className="w-10 h-10 bg-cyan-50 dark:bg-cyan-950/40 rounded-2xl flex items-center justify-center text-cyan-600">
                                                <div className="text-[10px] font-bold leading-tight text-center">
                                                    {new Date(session.start).toLocaleDateString([], { day: '2-digit' })}<br />
                                                    {new Date(session.start).toLocaleDateString([], { month: 'short' }).toUpperCase()}
                                                </div>
                                            </div>
                                            <div>
                                                <div className="text-sm font-bold truncate max-w-[180px]">{session.summary}</div>
                                                <div className="text-[10px] text-slate-400 font-medium">
                                                    {formatDate(session.start)} • {formatTime(session.start)}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="w-8 h-8 rounded-full bg-emerald-50 dark:bg-emerald-950/30 flex items-center justify-center text-emerald-500">
                                            <CheckCircle2 size={16} />
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                </div>

                {/* Footer */}
                <div className="p-6 border-t border-slate-100 dark:border-slate-700 bg-white dark:bg-slate-800 flex justify-center">
                    <button
                        onClick={onClose}
                        className="px-12 py-3 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 rounded-[1.5rem] text-sm font-bold transition-all hover:opacity-90 active:scale-95"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SchedulingModal;
