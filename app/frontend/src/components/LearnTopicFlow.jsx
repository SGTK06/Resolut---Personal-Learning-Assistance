import React, { useState } from 'react';
import {
    CheckCircle2,
    Upload,
    Loader2,
    AlertCircle,
    FileText
} from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL } from '../api';

const LearnTopicFlow = ({ onCancel }) => {
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Form State
    const [topic, setTopic] = useState('');
    const [focusArea, setFocusArea] = useState('');
    const [prerequisites, setPrerequisites] = useState([]);
    const [knownPrerequisites, setKnownPrerequisites] = useState({});
    const [files, setFiles] = useState([]);

    const handleFetchPrerequisites = async () => {
        if (!topic || !focusArea) return;
        setLoading(true);
        setError(null);
        try {
            const response = await axios.post(`${API_BASE_URL}/api/prerequisites`, {
                topic,
                focus_area: focusArea
            });
            setPrerequisites(response.data.prerequisites);
            setStep(3);
        } catch (err) {
            const errorMessage = err.response?.data?.error || err.response?.data?.message || err.message || 'Failed to fetch prerequisites. Please ensure backend is running.';
            setError(errorMessage);
            console.error('Error fetching prerequisites:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleFileUpload = (e) => {
        setFiles([...e.target.files]);
    };

    const handleSubmitAll = async () => {
        setLoading(true);
        setError(null);
        try {
            // 1. Upload Materials (if any)
            if (files.length > 0) {
                const formData = new FormData();
                formData.append('topic', topic);
                files.forEach(file => {
                    formData.append('files', file);
                });

                await axios.post(`${API_BASE_URL}/api/upload-materials`, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
            }

            // 2. Prepare Prerequisite Lists
            const known = [];
            const unknown = [];
            prerequisites.forEach((item, idx) => {
                if (knownPrerequisites[idx] === true) {
                    known.push(item);
                } else {
                    unknown.push(item);
                }
            });

            // 3. Generate Roadmap
            // Note: We use the local proxy /api/planning which forwards to AI service
            const planningResponse = await axios.post(`${API_BASE_URL}/api/planning`, {
                topic,
                focus_area: focusArea,
                prerequisites_known: known,
                prerequisites_unknown: unknown
            });

            const roadmap = planningResponse.data.roadmap;

            // Validate that we actually got a roadmap
            if (!roadmap || Object.keys(roadmap).length === 0) {
                throw new Error('Roadmap generation returned empty result. Please try again.');
            }

            // 4. Save Roadmap Locally
            await axios.post(`${API_BASE_URL}/api/roadmaps`, {
                topic,
                roadmap: roadmap
            });

            setStep(5); // Success step
        } catch (err) {
            const msg = err.response?.data?.detail || err.message || 'Failed to generate roadmap';
            setError('Error: ' + msg);
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white dark:bg-slate-800 rounded-3xl shadow-xl shadow-slate-200/50 dark:shadow-black/20 p-8 border border-slate-100 dark:border-slate-700 animate-fade-in-up">
            {/* Progress Bar */}
            <div className="flex gap-2 mb-8">
                {[1, 2, 3, 4].map((i) => (
                    <div
                        key={i}
                        className={`h-2 flex-1 rounded-full transition-all duration-500 ${step >= i
                            ? 'bg-gradient-to-r from-cyan-400 to-cyan-600'
                            : 'bg-slate-100 dark:bg-slate-700'
                            }`}
                    />
                ))}
            </div>

            {error && (
                <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-red-600 flex items-center gap-2 animate-shake">
                    <AlertCircle size={20} />
                    <span>{error}</span>
                </div>
            )}

            {/* Step 1: Topic */}
            {step === 1 && (
                <div className="space-y-6">
                    <h2 className="text-2xl font-bold dark:text-white">What do you want to learn?</h2>
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Topic Name</label>
                        <input
                            type="text"
                            value={topic}
                            onChange={(e) => setTopic(e.target.value)}
                            placeholder="e.g. Machine Learning, Ancient History, React Development"
                            className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-600 dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 outline-none transition-all"
                            autoFocus
                        />
                    </div>
                    <button
                        disabled={!topic}
                        onClick={() => setStep(2)}
                        className="w-full bg-cyan-600 text-white py-4 rounded-xl font-bold hover:bg-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-cyan-500/30"
                    >
                        Continue
                    </button>
                </div>
            )}

            {/* Step 2: Focus Area */}
            {step === 2 && (
                <div className="space-y-6">
                    <h2 className="text-2xl font-bold dark:text-white">Any specific parts to focus on?</h2>
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Specific Areas (Optional)</label>
                        <textarea
                            value={focusArea}
                            onChange={(e) => setFocusArea(e.target.value)}
                            placeholder="e.g. Neural Networks, The Industrial Revolution, State Management"
                            className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-600 dark:bg-slate-700 dark:text-white focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500 outline-none transition-all h-32"
                            autoFocus
                        />
                    </div>
                    <button
                        onClick={handleFetchPrerequisites}
                        disabled={loading}
                        className="w-full bg-cyan-600 text-white py-4 rounded-xl font-bold hover:bg-cyan-700 flex items-center justify-center gap-2 transition-all shadow-lg shadow-cyan-500/30"
                    >
                        {loading ? <Loader2 className="animate-spin" /> : "Check Prerequisites"}
                    </button>
                </div>
            )}

            {/* Step 3: Prerequisites */}
            {step === 3 && (
                <div className="space-y-6">
                    <h2 className="text-2xl font-bold dark:text-white">Do you know these prerequisites?</h2>
                    <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-2">
                        {prerequisites.map((item, idx) => (
                            <div key={idx} className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700/50 rounded-xl border border-slate-100 dark:border-slate-700">
                                <span className="font-medium dark:text-white">{item}</span>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => setKnownPrerequisites({ ...knownPrerequisites, [idx]: true })}
                                        className={`px-4 py-2 rounded-lg font-medium transition-all ${knownPrerequisites[idx] === true
                                            ? 'bg-teal-100 text-teal-700 border border-teal-200 shadow-sm'
                                            : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-600 hover:border-teal-300'
                                            }`}
                                    >
                                        Yes
                                    </button>
                                    <button
                                        onClick={() => setKnownPrerequisites({ ...knownPrerequisites, [idx]: false })}
                                        className={`px-4 py-2 rounded-lg font-medium transition-all ${knownPrerequisites[idx] === false
                                            ? 'bg-red-100 text-red-700 border border-red-200 shadow-sm'
                                            : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-600 hover:border-red-300'
                                            }`}
                                    >
                                        No
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                    <button
                        onClick={() => setStep(4)}
                        className="w-full bg-cyan-600 text-white py-4 rounded-xl font-bold hover:bg-cyan-700 transition-all shadow-lg shadow-cyan-500/30"
                    >
                        Next: Study Materials
                    </button>
                </div>
            )}

            {/* Step 4: Materials */}
            {step === 4 && (
                <div className="space-y-6">
                    <h2 className="text-2xl font-bold dark:text-white">Got any course materials?</h2>
                    <p className="text-slate-500 dark:text-slate-400">Upload PDF documents to help AI personalize your roadmap. The AI will scan them to tailor the plan.</p>

                    <div className="border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-3xl p-8 flex flex-col items-center justify-center space-y-4 hover:border-cyan-400 hover:bg-cyan-50/50 dark:hover:bg-cyan-900/10 transition-all cursor-pointer relative group">
                        <input
                            type="file"
                            multiple
                            accept=".pdf"
                            onChange={handleFileUpload}
                            className="absolute inset-0 opacity-0 cursor-pointer"
                        />
                        <div className="w-16 h-16 bg-cyan-50 dark:bg-cyan-900/20 rounded-full flex items-center justify-center text-cyan-600 group-hover:scale-110 transition-all">
                            <Upload size={32} />
                        </div>
                        <div className="text-center">
                            <span className="font-bold text-slate-700 dark:text-white group-hover:text-cyan-700 dark:group-hover:text-cyan-400 transition-colors">Click to upload</span>
                            <p className="text-sm text-slate-500">or drag and drop PDFs here</p>
                        </div>
                    </div>

                    {files.length > 0 && (
                        <div className="space-y-2">
                            <p className="text-sm font-medium text-slate-500 uppercase tracking-wider">Selected Files</p>
                            {files.map((file, idx) => (
                                <div key={idx} className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-700/50 rounded-xl border border-slate-200 dark:border-slate-600">
                                    <FileText className="text-cyan-600" size={20} />
                                    <span className="text-slate-700 dark:text-white flex-1 truncate">{file.name}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    <div className="flex gap-4">
                        <button
                            onClick={handleSubmitAll}
                            disabled={loading}
                            className="flex-1 py-4 text-slate-600 dark:text-slate-400 font-bold hover:bg-slate-50 dark:hover:bg-slate-700 rounded-xl transition-all"
                        >
                            Skip Upload
                        </button>
                        <button
                            onClick={handleSubmitAll}
                            disabled={loading}
                            className="flex-1 bg-cyan-600 text-white py-4 rounded-xl font-bold hover:bg-cyan-700 flex items-center justify-center gap-2 transition-all disabled:opacity-50 shadow-lg shadow-cyan-500/30"
                        >
                            {loading ? <Loader2 className="animate-spin" /> : (files.length > 0 ? "Upload & Generate" : "Generate Roadmap")}
                        </button>
                    </div>
                </div>
            )}

            {/* Step 5: Success */}
            {step === 5 && (
                <div className="text-center space-y-6 py-8 animate-fade-in-up">
                    <div className="w-24 h-24 bg-teal-100 dark:bg-teal-900/20 rounded-full flex items-center justify-center text-teal-600 mx-auto shadow-lg shadow-teal-500/20">
                        <CheckCircle2 size={48} />
                    </div>
                    <div className="space-y-2">
                        <h2 className="text-3xl font-bold dark:text-white">Roadmap Ready!</h2>
                        <p className="text-slate-500 dark:text-slate-400 text-lg">Your learning path for <span className="text-cyan-600 font-bold">"{topic}"</span> has been created.</p>
                    </div>
                    <button
                        onClick={onCancel} // This essentially goes back to Dashboard in parent context
                        className="w-full bg-slate-900 dark:bg-white dark:text-slate-900 text-white py-4 rounded-xl font-bold hover:opacity-90 max-w-sm mx-auto block transition-all shadow-xl"
                    >
                        View Dashboard
                    </button>
                </div>
            )}
        </div>
    );
};

export default LearnTopicFlow;
