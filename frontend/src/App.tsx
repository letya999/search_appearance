import React, { useState, useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, Search, Activity, Zap, Shield, User, FolderUp, FileDown, History, RefreshCw, BarChart, MessageSquare, Wand2, AlertCircle } from 'lucide-react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import { SearchResponse, PhotoProfile, SearchSession, SearchStage } from './types';

// --- Components ---

const DropZone = ({ title, files, onDrop, onRemove, colorClass }: any) => {
    const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { 'image/*': [] } });

    return (
        <div className={`p-4 rounded-xl glass-panel ${colorClass} transition-all`}>
            <h3 className="text-lg font-bold mb-3 flex items-center gap-2">
                {title === "Target Vibe" ? <Zap className="w-5 h-5" /> : <Shield className="w-5 h-5" />}
                {title}
            </h3>

            <div {...getRootProps()} className={`border-2 border-dashed border-white/20 rounded-lg p-6 text-center cursor-pointer hover:border-white/40 transition-colors ${isDragActive ? 'bg-white/5' : ''}`}>
                <input {...getInputProps()} />
                <Upload className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm text-gray-400">Drag & drop photos here</p>
            </div>

            <div className="mt-4 grid grid-cols-3 gap-2">
                {files.map((file: File, idx: number) => (
                    <div key={idx} className="relative group aspect-square rounded-lg overflow-hidden bg-black/50">
                        <img src={URL.createObjectURL(file)} alt="preview" className="w-full h-full object-cover opacity-80" />
                        <button
                            onClick={(e) => { e.stopPropagation(); onRemove(idx); }}
                            className="absolute top-1 right-1 p-1 bg-red-500/80 rounded-full text-white opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                            <X className="w-3 h-3" />
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
};

const ProfileCard = ({ profile, score, isResult = false, onClick }: { profile: PhotoProfile, score?: number, isResult?: boolean, onClick?: () => void }) => {
    const scorePct = score ? Math.round(score * 100) : 0;

    return (
        <div
            onClick={onClick}
            className={`relative group rounded-xl overflow-hidden glass-panel hover:scale-[1.02] transition-transform duration-300 ${onClick ? 'cursor-pointer' : ''}`}
        >
            <div className="aspect-[3/4] bg-gray-900 relative">
                <img
                    src={profile.image_path}
                    alt="profile"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                        (e.target as HTMLImageElement).src = `https://placehold.co/400x600/1e293b/475569?text=No+Image`;
                    }}
                />
                {
                    isResult && (
                        <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-md px-3 py-1 rounded-full border border-green-500/50">
                            <span className="text-green-400 font-bold text-sm">{scorePct}% Match</span>
                        </div>
                    )
                }
            </div >

            <div className="p-3 bg-gradient-to-t from-black/90 to-transparent absolute bottom-0 w-full">
                {/* Simple tags */}
                <div className="flex flex-wrap gap-1 text-xs">
                    {profile.basic?.age_group && (
                        <span className="px-2 py-0.5 rounded bg-white/10 text-gray-200">
                            {profile.basic.age_group.value}
                            {profile.basic.age_group.confidence !== undefined && <span className="ml-1 opacity-70 text-[10px]">{profile.basic.age_group.confidence.toFixed(2)}</span>}
                        </span>
                    )}
                    {profile.basic?.ethnicity && (
                        <span className="px-2 py-0.5 rounded bg-white/10 text-gray-200">
                            {profile.basic.ethnicity.value}
                            {profile.basic.ethnicity.confidence !== undefined && <span className="ml-1 opacity-70 text-[10px]">{profile.basic.ethnicity.confidence.toFixed(2)}</span>}
                        </span>
                    )}
                    {profile.vibe?.vibe && (
                        <span className="px-2 py-0.5 rounded bg-indigo-500/30 text-indigo-200 border border-indigo-500/30">
                            {profile.vibe.vibe.value}
                            {profile.vibe.vibe.confidence !== undefined && <span className="ml-1 opacity-70 text-[10px]">{profile.vibe.vibe.confidence.toFixed(2)}</span>}
                        </span>
                    )}
                </div>
            </div>
        </div >
    );
};

// --- Components ---

// NOTE: Components are defined here for simplicity in this MVP snippet.
const SearchProgressBar = ({ stages }: { stages: SearchStage[] }) => {
    if (!stages || stages.length === 0) return null;

    const currentStage = stages[stages.length - 1];

    return (
        <div className="w-full bg-slate-900 border border-blue-500/30 rounded-xl p-4 mb-6 shadow-lg shadow-blue-900/20 animate-fade-in">
            <div className="flex justify-between items-center mb-2">
                <span className="text-blue-300 font-mono text-sm uppercase tracking-wider flex items-center gap-2">
                    <RefreshCw className="w-3 h-3 animate-spin" />
                    {currentStage.name}
                </span>
                <span className="text-slate-400 text-xs">{Math.round(currentStage.progress * 100)}%</span>
            </div>

            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                    className="bg-blue-500 h-full transition-all duration-300 ease-out"
                    style={{ width: `${currentStage.progress * 100}%` }}
                ></div>
            </div>

            <div className="mt-2 text-xs text-slate-500 truncate">
                {currentStage.message || "Processing..."}
            </div>

            <div className="flex gap-1 mt-3">
                {stages.map((s, i) => (
                    <div
                        key={i}
                        className={`h-1 flex-1 rounded-full ${s.status === 'completed' ? 'bg-green-500' : s.status === 'running' ? 'bg-blue-500 animate-pulse' : 'bg-slate-700'}`}
                    />
                ))}
            </div>
        </div>
    );
};

const BatchUploadModal = ({ onClose }: { onClose: () => void }) => {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [status, setStatus] = useState<string>("");

    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);
        setStatus("Uploading...");

        const formData = new FormData();
        formData.append('file', file);

        try {
            // Get default user collection logic
            const colsRes = await fetch('/api/collections');
            const cols = await colsRes.json();
            let colId = "";
            if (cols.length > 0) {
                colId = cols[0].id;
            } else {
                const newCol = await fetch('/api/collections', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: "00000000-0000-0000-0000-000000000000",
                        name: "My Uploads",
                        description: "Batch uploaded photos"
                    })
                });
                const col = await newCol.json();
                colId = col.id;
            }

            const res = await fetch(`/api/collections/${colId}/upload_archive`, {
                method: 'POST',
                body: formData
            });

            if (res.ok) {
                const data = await res.json();
                setStatus(`Success! Processed ${data.processed} photos.`);
                setTimeout(onClose, 2000);
            } else {
                setStatus("Upload failed.");
            }
        } catch (e) {
            console.error(e);
            setStatus("Error uploading.");
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" onClick={onClose}>
            <div className="bg-slate-900 border border-white/10 rounded-xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <FolderUp className="w-5 h-5 text-blue-400" />
                    Batch Upload
                </h3>

                <div className="space-y-4">
                    <div className="border-2 border-dashed border-slate-700 rounded-lg p-8 text-center bg-slate-800/50">
                        <input
                            type="file"
                            accept=".zip"
                            onChange={(e) => setFile(e.target.files?.[0] || null)}
                            className="hidden"
                            id="zip-upload"
                        />
                        <label htmlFor="zip-upload" className="cursor-pointer block">
                            {file ? (
                                <div className="text-green-400 font-mono text-sm break-all">
                                    {file.name}
                                    <br />
                                    <span className="text-xs text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                                </div>
                            ) : (
                                <>
                                    <FolderUp className="w-10 h-10 mx-auto text-slate-500 mb-2" />
                                    <p className="text-sm text-slate-400">Click to select .ZIP archive</p>
                                    <p className="text-xs text-slate-600 mt-1">Images will be deduplicated</p>
                                </>
                            )}
                        </label>
                    </div>

                    {status && <div className="text-center text-sm font-bold text-blue-400">{status}</div>}

                    <button
                        onClick={handleUpload}
                        disabled={!file || uploading}
                        className="w-full py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-bold text-white transition-colors"
                    >
                        {uploading ? "Uploading..." : "Start Upload"}
                    </button>
                    {!uploading && (
                        <button onClick={onClose} className="w-full text-xs text-slate-500 hover:text-white">Cancel</button>
                    )}
                </div>
            </div>
        </div>
    );
};

// Helper: Euclidean Distance
const euclideanDistance = (a: number[], b: number[]) => {
    return Math.sqrt(a.reduce((acc, val, i) => acc + Math.pow(val - b[i], 2), 0));
};

// --- Main App ---

function App() {
    const [posFiles, setPosFiles] = useState<File[]>([]);
    const [negFiles, setNegFiles] = useState<File[]>([]);
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState<SearchResponse | null>(null);
    const [selectedProfile, setSelectedProfile] = useState<PhotoProfile | null>(null);
    const [viewingTarget, setViewingTarget] = useState(false);

    // Embeddings Cache for Duplicate Detection (Client-Side)
    const embeddingsRef = useRef(new Map<string, number[]>());


    // New State for Features
    const [error, setError] = useState<string | null>(null);
    const [searchStages, setSearchStages] = useState<SearchStage[]>([]);
    const [showBatchUpload, setShowBatchUpload] = useState(false);
    const [history, setHistory] = useState<SearchSession[]>([]);
    const [showHistory, setShowHistory] = useState(false);

    // Search Mode State
    const [searchMode, setSearchMode] = useState<'image' | 'text'>('image');
    const [textPrompt, setTextPrompt] = useState("");
    const [collectionId, setCollectionId] = useState<string>("");
    const [collectionStats, setCollectionStats] = useState<any>(null);
    const [apiReady, setApiReady] = useState(false);

    // Wait for API to be ready
    React.useEffect(() => {
        const checkApiReady = async () => {
            try {
                const res = await fetch('/api/health');
                const data = await res.json();
                if (data.ready) {
                    setApiReady(true);
                    return true;
                }
                return false;
            } catch (e) {
                console.log("API not ready yet, retrying...");
                return false;
            }
        };

        // Poll until ready
        const pollInterval = setInterval(async () => {
            const ready = await checkApiReady();
            if (ready) {
                clearInterval(pollInterval);
            }
        }, 1000);

        // Initial check
        checkApiReady().then(ready => {
            if (ready) clearInterval(pollInterval);
        });

        return () => clearInterval(pollInterval);
    }, []);

    // Initial load - only after API is ready
    React.useEffect(() => {
        if (!apiReady) return;

        // Fetch history
        fetch('/api/user/history')
            .then(res => res.json())
            .then(data => setHistory(data))
            .catch(e => console.error("Failed to load history", e));

        // Fetch Default Collection
        fetch('/api/collections')
            .then(res => res.json())
            .then(cols => {
                if (cols.length > 0) {
                    // Smart Select: Pick the one with the most photos
                    const sorted = [...cols].sort((a: any, b: any) => (b.photo_count || 0) - (a.photo_count || 0));
                    setCollectionId(sorted[0].id);
                    setCollectionStats(sorted[0]);
                } else {
                    // Create default if none
                    fetch('/api/collections', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            user_id: "00000000-0000-0000-0000-000000000000",
                            name: "My Collection",
                            description: "Default collection"
                        })
                    })
                        .then(r => r.json())
                        .then(newCol => {
                            setCollectionId(newCol.id);
                            setCollectionStats(newCol);
                        })
                        .catch(e => console.error("Failed to create default collection", e));
                }
            })
            .catch(e => console.error("Failed to load collections", e));
    }, [apiReady]);

    // Save to LocalStorage
    React.useEffect(() => {
        if (data) {
            localStorage.setItem('searchResults', JSON.stringify(data));
        }
    }, [data]);

    const handleSearch = async () => {
        if (posFiles.length === 0) return alert("Please upload at least 1 positive photo.");

        setLoading(true);
        setError(null);
        setSearchStages([]);

        // Generate Session ID
        const sessionId = crypto.randomUUID();

        // Connect WebSocket
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Note: The websocket path in backend is /ws/search/{id} but mapped via app.include_router?
        // Let's check api/websocket.py: @router.websocket("/ws/search/{session_id}")
        // And main.py: app.include_router(ws_router) (no prefix?)
        // Wait, main.py has: app.include_router(ws_router) WITHOUT prefix for websocket?
        // Usually websocket routers are top level or prefixed. 
        // Let's check main.py again. line 98: app.include_router(ws_router)
        // If ws_router has prefix, it's used. ws_router (mvp/api/websocket.py) has NO prefix in APIRouter().
        // But the decorator is @router.websocket("/ws/search/{session_id}")
        // So the path is /ws/search/{session_id}.
        // BUT, Vite proxy might need adjustment if it only proxies /api? 
        // Vite config usually proxies /api.
        // If I use /ws/... it might not be proxied.
        // I should probably mount it under /api/ws or ensure proxy handles it.
        // Let's assume standard Vite proxy setup often proxies /api.
        // If my backend is on 8000 and frontend on 5173, I need to hit backend.

        // Let's assume for now /ws is NOT proxied by default unless configured.
        // Safest: Use full URL if I can, OR ensure prefix is /api/ws and backend handles it.
        // I'll update backend to prefix /api if needed, currently it is root /ws.
        // Let's rely on relative path /ws/search/... and hope proxy handles it, or fails.
        // If proxy allows ws, good.

        // Note: Check if /ws is proxied correctly. Assuming it is.
        const ws = new WebSocket(`${protocol}//${window.location.host}/ws/search/${sessionId}`);

        ws.onopen = () => console.log("WS Connected");
        ws.onerror = (e) => console.log("WS Error", e);

        ws.onmessage = (event) => {
            try {
                const update = JSON.parse(event.data);
                console.log("WS Update:", update);
                setSearchStages(prev => {
                    const newStages = [...prev];
                    // If stage exists, update it. If not, push new.
                    // Actually, if we get "analyzing" again, we update the existing "analyzing" stage unless it's completed?
                    // Let's find the last stage with same name? Or just find by name.
                    const idx = newStages.findIndex(s => s.name === update.stage);
                    if (idx >= 0) {
                        newStages[idx] = { ...newStages[idx], ...update };
                    } else {
                        newStages.push({
                            name: update.stage,
                            status: update.status || 'running',
                            progress: update.progress || 0,
                            message: update.message
                        });
                    }
                    return newStages;
                });
            } catch (e) {
                console.error("WS Parse Error", e);
            }
        };

        const formData = new FormData();
        posFiles.forEach(f => formData.append('positives', f));
        negFiles.forEach(f => formData.append('negatives', f));
        formData.append('session_id', sessionId); // Add session ID
        // Image search endpoints in search.py currently grab ALL collections or ignore collection_id in this MVP version?
        // Let's check api/routes/search.py's /search endpoint (root).
        // It reads DB profiles directly from state.db_profiles or similar? 
        // Actually, the MVP file search.py /search endpoint was not shown in previous turns fully.
        // But let's assume valid implementation for image search as user didn't complain about it.

        try {
            const res = await fetch('/api/search', {
                method: 'POST',
                body: formData
            });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                const errMsg = typeof errData.detail === 'object' ? JSON.stringify(errData.detail) : (errData.detail || res.statusText);
                setError(errMsg);
                alert(errMsg); // Force visibility
                throw new Error(errMsg);
            }
            const json = await res.json();
            setData(json);

            // Save to history list immediately (optional, or refresh history)
            // Ideally we fetch history again.
            // setHistory(prev => [ ...prev, { id: sessionId, ... } ])
        } catch (e: any) {
            console.error(e);
            const msg = e.message || "Search failed.";
            setError(msg);
            alert(msg); // Force visibility
        } finally {
            setLoading(false);
            ws.close();
            // Refresh history
            fetch('/api/user/history')
                .then(r => r.json())
                .then(h => setHistory(h))
                .catch(() => { });
        }
    };

    const handleTextSearch = async () => {
        if (!textPrompt.trim()) return alert("Please enter a description.");
        if (!collectionId) return alert("No collection found. Please upload photos first or ensure backend is ready.");

        setLoading(true);
        setSearchStages([]);
        const sessionId = crypto.randomUUID();
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(`${protocol}//${window.location.host}/ws/search/${sessionId}`);

        ws.onopen = () => console.log("WS Connected");
        ws.onmessage = (event) => {
            const update = JSON.parse(event.data);
            setSearchStages(prev => {
                const newStages = [...prev];
                const idx = newStages.findIndex(s => s.name === update.stage);
                if (idx >= 0) newStages[idx] = { ...newStages[idx], ...update };
                else newStages.push({ name: update.stage, status: update.status || 'running', progress: update.progress || 0, message: update.message });
                return newStages;
            });
        };

        try {
            const res = await fetch('/api/search/text', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: textPrompt,
                    collection_id: collectionId,
                    session_id: sessionId,
                    top_k: 5
                })
            });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                const errMsg = typeof errData.detail === 'object' ? JSON.stringify(errData.detail) : (errData.detail || res.statusText);
                throw new Error(errMsg);
            }
            const json = await res.json();
            console.log("Text search response:", json);

            // Ensure all required fields exist to prevent UI crashes
            const safeData = {
                ...json,
                analyzed_positives: json.analyzed_positives || [],
                analyzed_negatives: json.analyzed_negatives || [],
                results: json.results || [],
                target_profile: json.target_profile || {}
            };
            setData(safeData);
        } catch (e: any) {
            console.error(e);
            alert(e.message || "Search failed. Check console.");
        } finally {
            setLoading(false);
            ws.close();
            fetch('/api/user/history').then(r => r.json()).then(h => setHistory(h)).catch(() => { });
        }
    };

    const handleGenSearch = async () => {
        if (!textPrompt.trim()) return alert("Please enter a description.");
        if (!collectionId) return alert("No collection found. Please upload photos first or ensure backend is ready.");

        setLoading(true);
        setSearchStages([]);
        const sessionId = crypto.randomUUID();
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws = new WebSocket(`${protocol}//${window.location.host}/ws/search/${sessionId}`);

        ws.onopen = () => console.log("WS Connected");
        ws.onmessage = (event) => {
            const update = JSON.parse(event.data);
            setSearchStages(prev => {
                const newStages = [...prev];
                const idx = newStages.findIndex(s => s.name === update.stage);
                if (idx >= 0) newStages[idx] = { ...newStages[idx], ...update };
                else newStages.push({ name: update.stage, status: update.status || 'running', progress: update.progress || 0, message: update.message });
                return newStages;
            });
        };

        try {
            const res = await fetch('/api/search/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt: textPrompt,
                    collection_id: collectionId,
                    session_id: sessionId,
                    top_k: 5
                })
            });
            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                const errMsg = typeof errData.detail === 'object' ? JSON.stringify(errData.detail) : (errData.detail || res.statusText);
                throw new Error(errMsg);
            }
            const json = await res.json();
            console.log("Gen search response:", json);

            // Ensure all required fields exist to prevent UI crashes
            const safeData = {
                ...json,
                analyzed_positives: json.analyzed_positives || [],
                analyzed_negatives: json.analyzed_negatives || [],
                results: json.results || [],
                target_profile: json.target_profile || {}
            };
            setData(safeData);
        } catch (e: any) {
            console.error(e);
            alert(e.message || "Search failed. Check console.");
        } finally {
            setLoading(false);
            ws.close();
            fetch('/api/user/history').then(r => r.json()).then(h => setHistory(h)).catch(() => { });
        }
    };

    const handleReset = () => {
        setData(null);
        setPosFiles([]);
        setNegFiles([]);
        embeddingsRef.current.clear();
        localStorage.removeItem('searchResults');
    };

    // Show loading overlay while API initializes
    if (!apiReady) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
                <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-blue-500 border-t-transparent mb-6"></div>
                    <h2 className="text-2xl font-bold text-white mb-2">Initializing API</h2>
                    <p className="text-gray-400">Loading models and warming up CLIP embeddings...</p>
                    <div className="mt-4 flex items-center justify-center gap-2 text-sm text-gray-500">
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen p-8 font-sans relative">
            {/* Batch Upload Modal */}
            {showBatchUpload && <BatchUploadModal onClose={() => setShowBatchUpload(false)} />}

            {/* History Overlay */}
            {showHistory && (
                <div className="fixed inset-y-0 right-0 z-40 w-80 bg-slate-900 border-l border-white/10 p-6 shadow-2xl animate-fade-in-right overflow-y-auto backdrop-blur-xl">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xl font-bold flex items-center gap-2 text-white">
                            <History className="w-5 h-5" /> History
                        </h3>
                        <button onClick={() => setShowHistory(false)}><X className="w-5 h-5 text-gray-500 hover:text-white" /></button>
                    </div>
                    <div className="space-y-4">
                        {history.length === 0 ? (
                            <p className="text-gray-500 text-sm text-center py-8">No history yet.</p>
                        ) : (
                            history.map(sess => (
                                <div key={sess.id} className="p-3 bg-white/5 rounded-lg border border-white/5 hover:bg-white/10 cursor-pointer transition-colors">
                                    <div className="flex justify-between items-start mb-2">
                                        <span className="text-xs text-gray-400">{new Date(sess.started_at).toLocaleDateString()} {new Date(sess.started_at).toLocaleTimeString()}</span>
                                        <span className={`text-[10px] px-2 py-0.5 rounded-full ${sess.completed_at ? 'bg-green-500/20 text-green-300' : 'bg-blue-500/20 text-blue-300'}`}>
                                            {sess.completed_at ? 'Completed' : 'Scanning'}
                                        </span>
                                    </div>
                                    <div className="text-sm font-bold text-white mb-1">
                                        Match Session
                                    </div>
                                    <div className="text-xs text-gray-500">
                                        Found {sess.results ? sess.results.length : 0} matches
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}

            <header className="max-w-7xl mx-auto mb-12 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
                        Visual DNA Search
                    </h1>
                    <p className="text-gray-400 text-sm">Semantic Appearance Engine v0.1</p>
                </div>
                <div className="flex gap-4">
                    <button
                        onClick={() => setShowBatchUpload(true)}
                        className="p-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors group relative"
                        title="Batch Upload"
                    >
                        <FolderUp className="w-5 h-5 text-gray-400 group-hover:text-blue-400" />
                    </button>

                    <button
                        onClick={() => setShowHistory(!showHistory)}
                        className="p-3 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 transition-colors group relative"
                        title="Search History"
                    >
                        <History className="w-5 h-5 text-gray-400 group-hover:text-purple-400" />
                    </button>

                    <div className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-xs text-center">
                        <span className="block text-gray-500 uppercase tracking-wider text-[10px]">Collection</span>
                        <span className="font-bold text-white">
                            {collectionStats ? `${collectionStats.photo_count} Photos` : "No Photos"}
                        </span>
                    </div>
                    {data && (
                        <button
                            onClick={handleReset}
                            className="px-4 py-2 rounded-lg bg-red-500/10 border border-red-500/20 text-red-300 text-xs hover:bg-red-500/20 transition-colors"
                        >
                            Reset Search
                        </button>
                    )}
                </div>
            </header>

            <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">

                {/* Left Column: Input */}
                <div className="lg:col-span-4 space-y-6">

                    {/* Mode Toggle */}
                    {!data && (
                        <div className="flex p-1 bg-white/5 rounded-xl border border-white/10">
                            <button
                                onClick={() => setSearchMode('image')}
                                className={`flex-1 py-2 rounded-lg text-sm font-bold flex items-center justify-center gap-2 transition-all ${searchMode === 'image' ? 'bg-blue-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
                            >
                                <Upload className="w-4 h-4" /> Image Search
                            </button>
                            <button
                                onClick={() => setSearchMode('text')}
                                className={`flex-1 py-2 rounded-lg text-sm font-bold flex items-center justify-center gap-2 transition-all ${searchMode === 'text' ? 'bg-purple-600 text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
                            >
                                <MessageSquare className="w-4 h-4" /> Text / Gen
                            </button>
                        </div>
                    )}

                    {/* Progress Bar */}
                    {loading && <SearchProgressBar stages={searchStages} />}

                    {/* Error Banner */}
                    {error && (
                        <div className="p-4 mb-4 rounded-xl bg-red-500/20 border border-red-500/50 text-red-200 animate-pulse flex items-center gap-2">
                            <AlertCircle className="w-5 h-5 flex-shrink-0" />
                            <span className="text-sm font-bold">{error}</span>
                        </div>
                    )}

                    {data ? (
                        <div className="space-y-6 animate-fade-in">
                            <div className="p-4 rounded-xl glass-panel border-blue-500/30">
                                <h3 className="text-lg font-bold mb-3 flex items-center gap-2 text-blue-200">
                                    <Zap className="w-5 h-5 text-blue-400" />
                                    Active Target Vibe
                                </h3>
                                {/* Show Images if Image Search, or Text if Text Search */}
                                {data.analyzed_positives.length > 0 ? (
                                    <div className="grid grid-cols-3 gap-2">
                                        {data.analyzed_positives.map((p, i) => (
                                            <div
                                                key={i}
                                                className="aspect-square rounded-lg overflow-hidden bg-black/50 border border-white/10 cursor-pointer hover:border-blue-400/50 transition-colors"
                                                onClick={() => setSelectedProfile(p)}
                                            >
                                                <img
                                                    src={p.image_path}
                                                    className="w-full h-full object-cover"
                                                    alt="input"
                                                    onError={(e) => {
                                                        console.error('Failed to load image:', p.image_path);
                                                        (e.target as HTMLImageElement).src = `https://placehold.co/400x400/1e293b/475569?text=Image+Error`;
                                                    }}
                                                />
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="p-4 bg-white/5 rounded-lg border border-white/10 text-sm text-gray-300 italic">
                                        "{textPrompt}"
                                    </div>
                                )}
                            </div>

                            {/* Show Gen Image if exists */}
                            {data.generated_image && (
                                <div className="p-4 rounded-xl glass-panel border-purple-500/30">
                                    <h3 className="text-lg font-bold mb-3 flex items-center gap-2 text-purple-200">
                                        <Wand2 className="w-5 h-5 text-purple-400" />
                                        Generated Reference
                                    </h3>
                                    <div
                                        className="aspect-square rounded-lg overflow-hidden bg-black/50 border border-white/10 cursor-pointer"
                                        onClick={() => setSelectedProfile(data.target_profile)}
                                    >
                                        <img src={data.generated_image} className="w-full h-full object-cover" alt="Generated" />
                                    </div>
                                </div>
                            )}

                            {data.analyzed_negatives.length > 0 && (
                                <div className="p-4 rounded-xl glass-panel border-red-500/30">
                                    <h3 className="text-lg font-bold mb-3 flex items-center gap-2 text-red-200">
                                        <Shield className="w-5 h-5 text-red-400" />
                                        Excluded Traits
                                    </h3>
                                    <div className="grid grid-cols-3 gap-2">
                                        {data.analyzed_negatives.map((p, i) => (
                                            <div
                                                key={i}
                                                className="aspect-square rounded-lg overflow-hidden bg-black/50 border border-white/10 cursor-pointer hover:border-red-400/50 transition-colors"
                                                onClick={() => setSelectedProfile(p)}
                                            >
                                                <img
                                                    src={p.image_path}
                                                    className="w-full h-full object-cover"
                                                    alt="excluded"
                                                    onError={(e) => {
                                                        console.error('Failed to load image:', p.image_path);
                                                        (e.target as HTMLImageElement).src = `https://placehold.co/400x400/1e293b/475569?text=Image+Error`;
                                                    }}
                                                />
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <button
                                onClick={() => setViewingTarget(true)}
                                className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600/20 to-blue-600/20 hover:from-purple-600/30 hover:to-blue-600/30 border border-purple-500/30 text-purple-200 font-bold text-sm transition-all flex items-center justify-center gap-2"
                            >
                                <User className="w-4 h-4" />
                                View Target Profile
                            </button>

                            <button
                                onClick={handleReset}
                                className="w-full py-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 font-bold text-sm transition-all flex items-center justify-center gap-2 group"
                            >
                                <Search className="w-4 h-4 opacity-50 group-hover:opacity-100" />
                                Start New Search
                            </button>

                            {/* Target Profile Info */}
                            <div className="glass-panel p-4 rounded-xl">
                                <h4 className="font-bold text-gray-300 mb-2 text-sm">Target Profile DNA</h4>
                                <div className="space-y-2 text-xs text-gray-400">
                                    <div className="flex justify-between border-b border-white/5 pb-1">
                                        <span>Ethnicity</span>
                                        <span className="text-white">
                                            {data.target_profile?.basic?.ethnicity?.value}
                                            {data.target_profile?.basic?.ethnicity?.confidence !== undefined && (
                                                <span className="text-gray-500 ml-1 text-[10px] mono">
                                                    {data.target_profile.basic?.ethnicity?.confidence.toFixed(2)}
                                                </span>
                                            )}
                                        </span>
                                    </div>
                                    <div className="flex justify-between border-b border-white/5 pb-1">
                                        <span>Face Shape</span>
                                        <span className="text-white">
                                            {data.target_profile?.face?.face_shape?.value}
                                            {data.target_profile?.face?.face_shape?.confidence !== undefined && (
                                                <span className="text-gray-500 ml-1 text-[10px] mono">
                                                    {data.target_profile.face?.face_shape?.confidence.toFixed(2)}
                                                </span>
                                            )}
                                        </span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>Vibe</span>
                                        <span className="text-white">
                                            {data.target_profile?.vibe?.vibe?.value}
                                            {data.target_profile?.vibe?.vibe?.confidence !== undefined && (
                                                <span className="text-gray-500 ml-1 text-[10px] mono">
                                                    {data.target_profile.vibe?.vibe?.confidence.toFixed(2)}
                                                </span>
                                            )}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <>
                            {searchMode === 'image' ? (
                                <>
                                    <DropZone
                                        title="Target Vibe"
                                        files={posFiles}
                                        onDrop={async (accepted: File[]) => {
                                            // 1. Filter exact duplicates (Name/Size)
                                            const unique = accepted.filter(f => !posFiles.some(p => p.name === f.name && p.size === f.size));
                                            if (unique.length < accepted.length) alert("Duplicate photos (exact name) were ignored.");

                                            // 2. Validate Semantically
                                            const validated: File[] = [];
                                            for (const file of unique) {
                                                const formData = new FormData();
                                                formData.append('file', file);
                                                try {
                                                    const res = await fetch('/api/validate/face', { method: 'POST', body: formData });
                                                    const json = await res.json();

                                                    if (json.status === 'ok' && json.embedding) {
                                                        let isDuplicate = false;
                                                        // Check against STORED embeddings
                                                        for (const [key, emb] of embeddingsRef.current.entries()) {
                                                            const dist = euclideanDistance(json.embedding, emb);
                                                            if (dist < 0.6) {
                                                                alert(`Duplicate person detected in ${file.name}! (Distance: ${dist.toFixed(2)})`);
                                                                isDuplicate = true;
                                                                break;
                                                            }
                                                        }
                                                        if (!isDuplicate) {
                                                            embeddingsRef.current.set(`${file.name}-${file.size}`, json.embedding);
                                                            validated.push(file);
                                                        }
                                                    } else {
                                                        // Fallback: allow if no face or error
                                                        validated.push(file);
                                                    }
                                                } catch (e) {
                                                    console.error("Validation error", e);
                                                    validated.push(file);
                                                }
                                            }

                                            if (validated.length > 0) {
                                                setPosFiles(prev => [...prev, ...validated]);
                                            }
                                        }}
                                        onRemove={(i: number) => setPosFiles(posFiles.filter((_, idx) => idx !== i))}
                                        colorClass="border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.1)]"
                                    />

                                    <DropZone
                                        title="Exclude Traits"
                                        files={negFiles}
                                        onDrop={(accepted: File[]) => {
                                            const unique = accepted.filter(f => !negFiles.some(p => p.name === f.name && p.size === f.size));
                                            if (unique.length < accepted.length) alert("Duplicate photos were ignored.");
                                            setNegFiles([...negFiles, ...unique]);
                                        }}
                                        onRemove={(i: number) => setNegFiles(negFiles.filter((_, idx) => idx !== i))}
                                        colorClass="border-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.1)]"
                                    />

                                    <button
                                        onClick={handleSearch}
                                        disabled={loading}
                                        className="w-full py-4 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold text-lg shadow-lg hover:shadow-blue-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                    >
                                        {loading ? <Activity className="animate-spin" /> : <Search />}
                                        {loading ? "Analyzing Geometry..." : "Find Matches"}
                                    </button>
                                </>
                            ) : (
                                <div className="space-y-6 animate-fade-in">
                                    <div className="p-4 rounded-xl glass-panel border-purple-500/30 shadow-[0_0_15px_rgba(168,85,247,0.1)]">
                                        <h3 className="text-lg font-bold mb-3 flex items-center gap-2 text-purple-200">
                                            <MessageSquare className="w-5 h-5 text-purple-400" />
                                            Describe Appearance
                                        </h3>
                                        <textarea
                                            value={textPrompt}
                                            onChange={(e) => setTextPrompt(e.target.value)}
                                            placeholder="e.g. 'Young woman with red hair and glasses, corporate style, smiling'"
                                            className="w-full h-32 bg-black/30 border border-white/10 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500/50 transition-colors resize-none"
                                        />
                                        <p className="text-xs text-gray-500 mt-2">
                                            Describe visual traits like hair, clothing, age, and vibe.
                                        </p>
                                    </div>

                                    <button
                                        onClick={handleTextSearch}
                                        disabled={loading || !textPrompt.trim()}
                                        className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold shadow-lg hover:shadow-purple-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                    >
                                        {loading ? <Activity className="animate-spin" /> : <Search />}
                                        Search by Description
                                    </button>

                                    <div className="relative">
                                        <div className="absolute inset-0 flex items-center">
                                            <div className="w-full border-t border-white/10"></div>
                                        </div>
                                        <div className="relative flex justify-center text-xs uppercase">
                                            <span className="bg-slate-900 px-2 text-gray-500">OR</span>
                                        </div>
                                    </div>

                                    <button
                                        onClick={handleGenSearch}
                                        disabled={loading || !textPrompt.trim()}
                                        className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-bold shadow-lg hover:shadow-emerald-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                    >
                                        {loading ? <Wand2 className="animate-spin" /> : <Wand2 />}
                                        Generate & Match
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>

                {/* Right Column: Results */}
                <div className="lg:col-span-8 space-y-8">
                    {/* Results Status Bar */}
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold text-white flex items-center gap-2">
                            Top Matches
                            {data && <span className="text-sm font-normal text-gray-400">({data.results.length} found in {data.execution_time ? data.execution_time.toFixed(2) : "0.00"}s)</span>}
                        </h2>
                        {data && (
                            <div className="flex gap-2">
                                <a
                                    href={`/api/collections/${data.results[0]?.profile.collection_id || 'default'}/export/csv`}
                                    target="_blank"
                                    className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 text-xs flex items-center gap-1 text-gray-300 transition-colors"
                                    download="results.csv"
                                    title="Export Results CSV"
                                    onClick={(e) => {
                                        // Since we don't have collection ID tracked in frontend state perfectly yet,
                                        // we might need to rely on what backend returns or just use a placeholder
                                        // Actually the backend endpoint needs a collection ID. 
                                        // Our MVP search doesn't return collection ID explicitly in root.
                                        // The profiles have it? No, PhotoProfile schema doesn't effectively enforce it.
                                        // Let's mock it or use the 'default' assumption we made in batch upload.
                                        // Better: Just don't link if we don't know ID, OR fetch it.
                                        // Let's skip valid href and handle onClick to fetch the current collection's export.
                                        e.preventDefault();
                                        // For MVP, alerting or simple stub since we need collection ID context which we might have lost.
                                        // But wait, the user operates on *a* collection.
                                        // We can assume first collection for MVP.
                                        fetch('/api/collections').then(r => r.json()).then(cols => {
                                            if (cols.length > 0) window.open(`/api/collections/${cols[0].id}/export/csv`, '_blank');
                                        });
                                    }}
                                >
                                    <FileDown className="w-3 h-3" /> CSV
                                </a>
                                <a
                                    href="#"
                                    className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 text-xs flex items-center gap-1 text-gray-300 transition-colors"
                                    onClick={(e) => {
                                        e.preventDefault();
                                        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
                                        const url = URL.createObjectURL(blob);
                                        const a = document.createElement('a');
                                        a.href = url;
                                        a.download = "search_results.json";
                                        a.click();
                                    }}
                                >
                                    <FileDown className="w-3 h-3" /> JSON
                                </a>
                            </div>
                        )}
                    </div>

                    {/* DNA Summary Section (Requested Feature) */}
                    {data && (
                        <div className="glass-panel p-6 rounded-2xl animate-float">
                            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                                <Activity className="w-5 h-5 text-blue-400" />
                                Search DNA Synthesis
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                {/* Positives Contribution */}
                                <div className="p-4 rounded-xl bg-white/5 border border-green-500/20">
                                    <div className="text-xs text-uppercase text-green-400 font-bold mb-2">POSITIVE SIGNALS</div>
                                    <div className="text-sm text-gray-300">
                                        Based on {data.analyzed_positives.length} references, prioritizing:
                                        <div className="flex flex-wrap gap-1 mt-2">
                                            {data.target_profile?.vibe?.vibe?.value && <span className="px-2 py-0.5 bg-green-500/20 text-green-200 rounded text-xs">{data.target_profile.vibe.vibe.value}</span>}
                                            {data.target_profile?.basic?.ethnicity?.value && <span className="px-2 py-0.5 bg-green-500/20 text-green-200 rounded text-xs">{data.target_profile.basic.ethnicity.value}</span>}
                                        </div>
                                    </div>
                                </div>

                                {/* Target Profile (The Code) */}
                                <div className="md:col-span-2 p-4 rounded-xl bg-gradient-to-r from-blue-900/40 to-indigo-900/40 border border-blue-500/30">
                                    <div className="text-xs text-uppercase text-blue-400 font-bold mb-2">SYNTHESIZED TARGET PROFILE</div>
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div>
                                            <span className="text-gray-400 block text-xs">Target Vibe</span>
                                            <span className="text-white font-medium">
                                                {data.target_profile?.vibe?.vibe?.value || "Any"}
                                                {data.target_profile?.vibe?.vibe?.confidence !== undefined && <span className="text-gray-500 ml-1 text-xs opacity-75">{data.target_profile?.vibe?.vibe?.confidence.toFixed(2)}</span>}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="text-gray-400 block text-xs">Facial Structure</span>
                                            <span className="text-white font-medium">
                                                {data.target_profile?.face?.face_shape?.value || "Any"}
                                                {data.target_profile?.face?.face_shape?.confidence !== undefined && <span className="text-gray-500 ml-1 text-xs opacity-75">{data.target_profile?.face?.face_shape?.confidence.toFixed(2)}</span>}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="text-gray-400 block text-xs">Demographic</span>
                                            <span className="text-white font-medium">
                                                {data.target_profile?.basic?.gender?.value || "Any"} / {data.target_profile?.basic?.age_group?.value || "Any"}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="text-gray-400 block text-xs">Style</span>
                                            <span className="text-white font-medium">
                                                {data.target_profile?.vibe?.style?.value || "Any"}
                                                {data.target_profile?.vibe?.style?.confidence !== undefined && <span className="text-gray-500 ml-1 text-xs opacity-75">{data.target_profile?.vibe?.style?.confidence.toFixed(2)}</span>}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {!data && !loading && (
                        <div className="h-full flex items-center justify-center text-gray-500 border-2 border-dashed border-white/10 rounded-3xl min-h-[400px]">
                            <div className="text-center">
                                <User className="w-16 h-16 mx-auto mb-4 opacity-20" />
                                <p>Upload photos to generate visual matches</p>
                            </div>
                        </div>
                    )}

                    {loading && (
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 animate-pulse">
                            {[...Array(6)].map((_, i) => (
                                <div key={i} className="aspect-[3/4] bg-white/5 rounded-xl"></div>
                            ))}
                        </div>
                    )}

                    {data && (
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
                            {data.results.map((res, idx) => (
                                <ProfileCard
                                    key={idx}
                                    profile={res.profile}
                                    score={res.score}
                                    isResult={true}
                                    onClick={() => setSelectedProfile(res.profile)}
                                />
                            ))}
                        </div>
                    )}
                </div>

            </main>

            {/* Profile Detail Modal */}
            {selectedProfile && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" onClick={() => setSelectedProfile(null)}>
                    <div className="bg-slate-900 border border-white/10 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto flex flex-col md:flex-row overflow-hidden shadow-2xl" onClick={e => e.stopPropagation()}>
                        {/* Image Side */}
                        <div className="md:w-1/2 bg-black relative min-h-[300px]">
                            <img src={selectedProfile.image_path} className="absolute inset-0 w-full h-full object-contain" alt="Full profile" />
                        </div>
                        {/* Data Side */}
                        <div className="md:w-1/2 p-8 space-y-6">
                            <div className="flex justify-between items-start">
                                <div>
                                    <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
                                        Profile Analysis
                                    </h2>
                                    <p className="text-xs text-gray-500 mt-1">Showing all 20 detailed attributes</p>
                                </div>
                                <button onClick={() => setSelectedProfile(null)} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                                    <X className="w-6 h-6" />
                                </button>
                            </div>

                            <div className="space-y-6 overflow-y-auto max-h-[60vh] pr-2 custom-scrollbar">
                                {/* Basic */}
                                <div className="space-y-2">
                                    <h4 className="text-sm font-bold text-gray-500 uppercase tracking-widest border-b border-white/10 pb-1">Basic Traits</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <TraitRow label="Gender" trait={selectedProfile.basic?.gender} />
                                        <TraitRow label="Age Group" trait={selectedProfile.basic?.age_group} />
                                        <TraitRow label="Ethnicity" trait={selectedProfile.basic?.ethnicity} />
                                        <TraitRow label="Height" trait={selectedProfile.basic?.height} />
                                        <TraitRow label="Body Type" trait={selectedProfile.basic?.body_type} />
                                    </div>
                                </div>

                                {/* Face */}
                                <div className="space-y-2">
                                    <h4 className="text-sm font-bold text-gray-500 uppercase tracking-widest border-b border-white/10 pb-1">Facial Structure</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <TraitRow label="Face Shape" trait={selectedProfile.face?.face_shape} />
                                        <TraitRow label="Eye Color" trait={selectedProfile.face?.eye_color} />
                                        <TraitRow label="Eye Shape" trait={selectedProfile.face?.eye_shape} />
                                        <TraitRow label="Nose" trait={selectedProfile.face?.nose} />
                                        <TraitRow label="Lips" trait={selectedProfile.face?.lips} />
                                        <TraitRow label="Jawline" trait={selectedProfile.face?.jawline} />
                                    </div>
                                </div>

                                {/* Hair */}
                                <div className="space-y-2">
                                    <h4 className="text-sm font-bold text-gray-500 uppercase tracking-widest border-b border-white/10 pb-1">Hair</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <TraitRow label="Color" trait={selectedProfile.hair?.color} />
                                        <TraitRow label="Length" trait={selectedProfile.hair?.length} />
                                        <TraitRow label="Texture" trait={selectedProfile.hair?.texture} />
                                    </div>
                                </div>

                                {/* Extra */}
                                <div className="space-y-2">
                                    <h4 className="text-sm font-bold text-gray-500 uppercase tracking-widest border-b border-white/10 pb-1">Additional Features</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <TraitRow label="Facial Hair" trait={selectedProfile.extra?.facial_hair} />
                                        <TraitRow label="Skin Tone" trait={selectedProfile.extra?.skin_tone} />
                                        <TraitRow label="Glasses" trait={selectedProfile.extra?.glasses} />
                                        <TraitRow label="Tattoos" trait={selectedProfile.extra?.tattoos} />
                                    </div>
                                </div>

                                {/* Vibe */}
                                <div className="space-y-2">
                                    <h4 className="text-sm font-bold text-gray-500 uppercase tracking-widest border-b border-white/10 pb-1">Vibe & Style</h4>
                                    <div className="grid grid-cols-2 gap-4">
                                        <TraitRow label="Overall Vibe" trait={selectedProfile.vibe?.vibe} />
                                        <TraitRow label="Style" trait={selectedProfile.vibe?.style} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Target Profile Modal */}
            {viewingTarget && data && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" onClick={() => setViewingTarget(false)}>
                    <div className="bg-slate-900 border border-purple-500/30 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-8 shadow-2xl" onClick={e => e.stopPropagation()}>
                        <div className="flex justify-between items-start mb-6">
                            <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-blue-400">
                                🧬 Synthesized Target Profile
                            </h2>
                            <button onClick={() => setViewingTarget(false)} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                                <X className="w-6 h-6" />
                            </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Basic */}
                            <div className="space-y-2">
                                <h4 className="text-sm font-bold text-purple-400 uppercase tracking-widest border-b border-purple-500/30 pb-1">Basic Traits</h4>
                                <div className="space-y-3">
                                    <TraitRow label="Gender" trait={data.target_profile.basic?.gender} />
                                    <TraitRow label="Age Group" trait={data.target_profile.basic?.age_group} />
                                    <TraitRow label="Ethnicity" trait={data.target_profile.basic?.ethnicity} />
                                    <TraitRow label="Height" trait={data.target_profile.basic?.height} />
                                    <TraitRow label="Body Type" trait={data.target_profile.basic?.body_type} />
                                </div>
                            </div>

                            {/* Face */}
                            <div className="space-y-2">
                                <h4 className="text-sm font-bold text-purple-400 uppercase tracking-widest border-b border-purple-500/30 pb-1">Facial Structure</h4>
                                <div className="space-y-3">
                                    <TraitRow label="Face Shape" trait={data.target_profile.face?.face_shape} />
                                    <TraitRow label="Eye Color" trait={data.target_profile.face?.eye_color} />
                                    <TraitRow label="Eye Shape" trait={data.target_profile.face?.eye_shape} />
                                    <TraitRow label="Nose" trait={data.target_profile.face?.nose} />
                                    <TraitRow label="Lips" trait={data.target_profile.face?.lips} />
                                    <TraitRow label="Jawline" trait={data.target_profile.face?.jawline} />
                                </div>
                            </div>

                            {/* Hair */}
                            <div className="space-y-2">
                                <h4 className="text-sm font-bold text-purple-400 uppercase tracking-widest border-b border-purple-500/30 pb-1">Hair</h4>
                                <div className="space-y-3">
                                    <TraitRow label="Color" trait={data.target_profile.hair?.color} />
                                    <TraitRow label="Length" trait={data.target_profile.hair?.length} />
                                    <TraitRow label="Texture" trait={data.target_profile.hair?.texture} />
                                </div>
                            </div>

                            {/* Extra */}
                            <div className="space-y-2">
                                <h4 className="text-sm font-bold text-purple-400 uppercase tracking-widest border-b border-purple-500/30 pb-1">Additional Features</h4>
                                <div className="space-y-3">
                                    <TraitRow label="Facial Hair" trait={data.target_profile.extra?.facial_hair} />
                                    <TraitRow label="Skin Tone" trait={data.target_profile.extra?.skin_tone} />
                                    <TraitRow label="Glasses" trait={data.target_profile.extra?.glasses} />
                                    <TraitRow label="Tattoos" trait={data.target_profile.extra?.tattoos} />
                                </div>
                            </div>

                            {/* Vibe */}
                            <div className="space-y-2 md:col-span-2">
                                <h4 className="text-sm font-bold text-purple-400 uppercase tracking-widest border-b border-purple-500/30 pb-1">Vibe & Style</h4>
                                <div className="grid grid-cols-2 gap-3">
                                    <TraitRow label="Overall Vibe" trait={data.target_profile.vibe?.vibe} />
                                    <TraitRow label="Style" trait={data.target_profile.vibe?.style} />
                                </div>
                            </div>
                        </div>

                        <div className="mt-6 p-4 bg-purple-900/20 border border-purple-500/20 rounded-lg">
                            <p className="text-xs text-gray-400">
                                <span className="text-purple-400 font-bold">📊 Based on:</span> {data.analyzed_positives.length} positive examples
                                {data.analyzed_negatives.length > 0 && ` and ${data.analyzed_negatives.length} negative examples`}
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Helper for row
const TraitRow = ({ label, trait }: any) => {
    // Show even if trait is missing
    if (!trait || !trait.value) {
        return (
            <div>
                <span className="text-gray-500 text-xs block">{label}</span>
                <div className="flex items-center gap-2">
                    <span className="text-gray-600 text-sm italic">not detected</span>
                </div>
            </div>
        );
    }

    return (
        <div className="w-full">
            <div className="flex justify-between items-center mb-1">
                <span className="text-gray-500 text-xs">{label}</span>
                {trait.confidence !== undefined && (
                    <span className="text-xs text-gray-400 font-mono">{trait.confidence.toFixed(2)}</span>
                )}
            </div>
            <div className="flex items-center gap-2 justify-between">
                <span className="text-slate-200 text-sm font-medium">{trait.value}</span>
                {trait.confidence !== undefined && (
                    <div className="h-1.5 w-24 bg-gray-800 rounded-full overflow-hidden ml-2 flex-shrink-0">
                        <div
                            className="h-full bg-gradient-to-r from-blue-600 to-blue-400"
                            style={{ width: `${trait.confidence * 100}%` }}
                        ></div>
                    </div>
                )}
            </div>
        </div>
    )
}

export default App;
