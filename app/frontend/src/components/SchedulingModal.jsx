import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { X, Loader2, Calendar, Settings, Zap, History, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
import { API_BASE_URL } from '../api';

const SchedulingModal = ({ isOpen, onClose, topic }) => {
    const [autoSettings, setAutoSettings] = useState({ auto_schedule: true, trigger_time: "00:00", last_run: null });
    const [saving, setSaving] = useState(false);
    const [scheduling, setScheduling] = useState(false);
    const [sessions, setSessions] = useState([]);
    const [fetchingSessions, setFetchingSessions] = useState(false);

    useEffect(() => {
        if (isOpen) {
            fetchSettings();
            fetchSessions();
        }
    }, [isOpen]);

    const fetchSettings = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/api/settings/scheduling`);
            setAutoSettings(response.data);
        } catch (err) {
            console.error("Failed to fetch settings:", err);
        }
    };

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

    const saveSettings = async (newSettings) => {
        setSaving(true);
        try {
            await axios.post(`${API_BASE_URL}/api/settings/scheduling`, newSettings);
            setAutoSettings(newSettings);
        } catch (err) {
            console.error("Failed to save settings:", err);
        } finally {
            setSaving(false);
        }
    };

    const handleScheduleNow = async () => {
        setScheduling(true);
        try {
            const response = await axios.post(`${API_BASE_URL}/api/calendar/trigger-now`);
            if (response.data.status === 'success') {
                // Refresh everything
                await fetchSettings();
                await fetchSessions();
            }
        } catch (err) {
            console.error("Manual scheduling failed:", err);
        } finally {
            setScheduling(false);
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
                            <Settings size={20} />
                        </div>
                        <div>
                            <h3 className="font-bold text-lg">Scheduling Settings</h3>
                            <p className="text-xs text-slate-500">Autonomous learning organizer</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-full transition-colors text-slate-400">
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-8 space-y-8 bg-slate-50/50 dark:bg-slate-900/30">
                    {/* Primary Action: Schedule Now */}
                    <div className="space-y-4">
                        <button
                            onClick={handleScheduleNow}
                            disabled={scheduling}
                            className="w-full py-5 bg-cyan-600 hover:bg-cyan-700 text-white rounded-[2rem] font-bold shadow-xl shadow-cyan-500/20 transition-all flex items-center justify-center gap-3 disabled:opacity-50"
                        >
                            {scheduling ? <Loader2 className="animate-spin" size={20} /> : <Zap size={20} />}
                            {scheduling ? "Consulting AI Agent..." : "Schedule Sessions Now"}
                        </button>
                        <p className="text-xs text-cyan-700 dark:text-cyan-300 mt-1 leading-relaxed">
                            The agent will automatically scan your calendar and book one 1-hour study session for the next 24 hours.
                        </p>
                    </div>

                    {/* Upcoming Sessions List */}
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                                <Calendar size={14} />
                                Upcoming Sessions (Next 24h)
                            </h4>
                            {fetchingSessions && <Loader2 size={12} className="animate-spin text-cyan-500" />}
                        </div>

                        <div className="space-y-3">
                            {sessions.length === 0 ? (
                                <div className="p-6 text-center bg-white dark:bg-slate-800 rounded-3xl border border-dashed border-slate-200 dark:border-slate-700 opacity-50">
                                    <p className="text-xs">No study sessions found for the next 2 days.</p>
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

                    {/* Automation Settings */}
                    <div className="space-y-4 pt-4 border-t border-slate-200/50 dark:border-slate-700/50">
                        <div className="flex items-center justify-between p-5 bg-white dark:bg-slate-800 rounded-3xl border border-slate-100 dark:border-slate-700 shadow-sm">
                            <div className="flex items-center gap-3">
                                <Clock className="text-slate-400" size={18} />
                                <span className="text-sm font-semibold">Daily Automation</span>
                            </div>
                            <button
                                onClick={() => saveSettings({ ...autoSettings, auto_schedule: !autoSettings.auto_schedule })}
                                disabled={saving}
                                className={`w-14 h-7 rounded-full p-1 transition-all duration-300 ${autoSettings.auto_schedule ? 'bg-cyan-600' : 'bg-slate-200 dark:bg-slate-700'}`}
                            >
                                <div className={`w-5 h-5 bg-white rounded-full shadow-md transition-transform duration-300 ${autoSettings.auto_schedule ? 'translate-x-7' : 'translate-x-0'}`} />
                            </button>
                        </div>

                        <div className="p-5 bg-white dark:bg-slate-800 rounded-3xl border border-slate-100 dark:border-slate-700 shadow-sm space-y-4">
                            <div className="flex justify-between items-center">
                                <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">Trigger Time</label>
                            </div>
                            <input
                                type="time"
                                value={autoSettings.trigger_time}
                                onChange={(e) => saveSettings({ ...autoSettings, trigger_time: e.target.value })}
                                className="w-full bg-slate-50 dark:bg-slate-900 border-none rounded-2xl p-4 text-lg font-bold text-cyan-600 focus:ring-2 focus:ring-cyan-500/20 text-center"
                            />
                        </div>

                        {/* Last Run Info */}
                        {autoSettings.last_run && (
                            <div className="flex items-center justify-center gap-2 py-2 px-4 bg-slate-100 dark:bg-slate-700/50 rounded-full w-fit mx-auto">
                                <History size={12} className="text-slate-400" />
                                <span className="text-[10px] font-medium text-slate-500 dark:text-slate-400 uppercase tracking-tighter">
                                    Last Sync: {new Date(autoSettings.last_run).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                                </span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-slate-100 dark:border-slate-700 bg-white dark:bg-slate-800 flex justify-center">
                    <button
                        onClick={onClose}
                        className="px-10 py-3 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 rounded-[1.5rem] text-sm font-bold transition-all"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

export default SchedulingModal;
