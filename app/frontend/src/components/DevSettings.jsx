import React, { useState, useEffect } from 'react';

const DevSettings = ({ onClose }) => {
    const [settings, setSettings] = useState({
        warning_interval_seconds: 180,
        negotiation_interval_seconds: 120
    });
    const [loading, setLoading] = useState(true);
    const [message, setMessage] = useState('');

    useEffect(() => {
        fetch('http://localhost:8000/api/dev/lockdown_settings')
            .then(res => res.json())
            .then(data => {
                setSettings(data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to load settings", err);
                setLoading(false);
            });
    }, []);

    const handleSave = () => {
        fetch('http://localhost:8000/api/dev/lockdown_settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        })
            .then(res => res.json())
            .then(data => {
                setMessage('Settings saved!');
                setTimeout(() => setMessage(''), 2000);
            })
            .catch(err => console.error("Failed to save settings", err));
    };

    if (loading) return <div className="p-4 bg-gray-900 text-white rounded-xl">Loading...</div>;

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
            <div className="bg-gray-900 border border-cyan-500/30 p-6 rounded-2xl w-[400px] shadow-2xl relative">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-400 hover:text-white"
                >
                    ✕
                </button>

                <h2 className="text-xl font-bold text-cyan-400 mb-6">Dev Mode: Intervention Settings</h2>

                <div className="space-y-6">
                    <div>
                        <label className="block text-gray-300 text-sm mb-2">
                            Warning Timeout (Seconds)
                            <span className="block text-xs text-gray-500">Wait time before "Scroll Mindfully" popup</span>
                        </label>
                        <input
                            type="range"
                            min="30"
                            max="300"
                            step="10"
                            value={settings.warning_interval_seconds}
                            onChange={(e) => setSettings({ ...settings, warning_interval_seconds: parseInt(e.target.value) })}
                            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                        />
                        <div className="text-right text-cyan-500 font-mono mt-1">{settings.warning_interval_seconds}s</div>
                    </div>

                    <div>
                        <label className="block text-gray-300 text-sm mb-2">
                            Negotiation Interval (Seconds)
                            <span className="block text-xs text-gray-500">Time between Warning and Negotiation</span>
                        </label>
                        <input
                            type="range"
                            min="30"
                            max="300"
                            step="10"
                            value={settings.negotiation_interval_seconds}
                            onChange={(e) => setSettings({ ...settings, negotiation_interval_seconds: parseInt(e.target.value) })}
                            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                        />
                        <div className="text-right text-cyan-500 font-mono mt-1">{settings.negotiation_interval_seconds}s</div>
                    </div>

                    <div className="pt-4 flex justify-between items-center">
                        <span className="text-green-400 text-sm">{message}</span>
                        <button
                            onClick={handleSave}
                            className="bg-cyan-600 hover:bg-cyan-500 text-white px-4 py-2 rounded-lg transition-colors font-medium"
                        >
                            Save Changes
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DevSettings;
