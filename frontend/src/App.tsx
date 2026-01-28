import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, Search, Activity, Zap, Shield, User } from 'lucide-react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import { SearchResponse, PhotoProfile } from './types';

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
                {isResult && (
                    <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-md px-3 py-1 rounded-full border border-green-500/50">
                        <span className="text-green-400 font-bold text-sm">{scorePct}% Match</span>
                    </div>
                )}
            </div>

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
        </div>
    );
};

// --- Main App ---

function App() {
    const [posFiles, setPosFiles] = useState<File[]>([]);
    const [negFiles, setNegFiles] = useState<File[]>([]);
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState<SearchResponse | null>(null);
    const [selectedProfile, setSelectedProfile] = useState<PhotoProfile | null>(null);
    const [viewingTarget, setViewingTarget] = useState(false);

    // Initialize from LocalStorage
    React.useEffect(() => {
        const saved = localStorage.getItem('searchResults');
        if (saved) {
            try {
                setData(JSON.parse(saved));
            } catch (e) {
                console.error("Failed to load saved state", e);
            }
        }
    }, []);

    // Save to LocalStorage
    React.useEffect(() => {
        if (data) {
            localStorage.setItem('searchResults', JSON.stringify(data));
        }
    }, [data]);

    const handleSearch = async () => {
        if (posFiles.length === 0) return alert("Please upload at least 1 positive photo.");

        setLoading(true);
        const formData = new FormData();
        posFiles.forEach(f => formData.append('positives', f));
        negFiles.forEach(f => formData.append('negatives', f));

        try {
            const res = await fetch('/api/search', {
                method: 'POST',
                body: formData
            });
            const json = await res.json();
            console.log('Search API Response:', json);
            console.log('Target Profile:', json.target_profile);
            console.log('Analyzed Positives:', json.analyzed_positives);
            console.log('Analyzed Negatives:', json.analyzed_negatives);
            setData(json);
        } catch (e) {
            console.error(e);
            alert("Search failed. Check console.");
        } finally {
            setLoading(false);
        }
    };

    const handleReset = () => {
        setData(null);
        setPosFiles([]);
        setNegFiles([]);
        localStorage.removeItem('searchResults');
    };

    return (
        <div className="min-h-screen p-8 font-sans">
            <header className="max-w-7xl mx-auto mb-12 flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
                        Visual DNA Search
                    </h1>
                    <p className="text-gray-400 text-sm">Semantic Appearance Engine v0.1</p>
                </div>
                <div className="flex gap-4">
                    <div className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-xs text-center">
                        <span className="block text-gray-500 uppercase tracking-wider text-[10px]">Database</span>
                        <span className="font-bold text-white">437 Profiles</span>
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

                    {data ? (
                        <div className="space-y-6 animate-fade-in">
                            <div className="p-4 rounded-xl glass-panel border-blue-500/30">
                                <h3 className="text-lg font-bold mb-3 flex items-center gap-2 text-blue-200">
                                    <Zap className="w-5 h-5 text-blue-400" />
                                    Active Target Vibe
                                </h3>
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
                            </div>

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
                                            {data.target_profile.basic?.ethnicity?.value}
                                            {data.target_profile.basic?.ethnicity?.confidence !== undefined && (
                                                <span className="text-gray-500 ml-1 text-[10px] mono">
                                                    {data.target_profile.basic?.ethnicity?.confidence.toFixed(2)}
                                                </span>
                                            )}
                                        </span>
                                    </div>
                                    <div className="flex justify-between border-b border-white/5 pb-1">
                                        <span>Face Shape</span>
                                        <span className="text-white">
                                            {data.target_profile.face?.face_shape?.value}
                                            {data.target_profile.face?.face_shape?.confidence !== undefined && (
                                                <span className="text-gray-500 ml-1 text-[10px] mono">
                                                    {data.target_profile.face?.face_shape?.confidence.toFixed(2)}
                                                </span>
                                            )}
                                        </span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>Vibe</span>
                                        <span className="text-white">
                                            {data.target_profile.vibe?.vibe?.value}
                                            {data.target_profile.vibe?.vibe?.confidence !== undefined && (
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
                            <DropZone
                                title="Target Vibe"
                                files={posFiles}
                                onDrop={(accepted: File[]) => setPosFiles([...posFiles, ...accepted])}
                                onRemove={(i: number) => setPosFiles(posFiles.filter((_, idx) => idx !== i))}
                                colorClass="border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.1)]"
                            />

                            <DropZone
                                title="Exclude Traits"
                                files={negFiles}
                                onDrop={(accepted: File[]) => setNegFiles([...negFiles, ...accepted])}
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
                                            {data.target_profile.vibe?.vibe?.value && <span className="px-2 py-0.5 bg-green-500/20 text-green-200 rounded text-xs">{data.target_profile.vibe.vibe.value}</span>}
                                            {data.target_profile.basic?.ethnicity?.value && <span className="px-2 py-0.5 bg-green-500/20 text-green-200 rounded text-xs">{data.target_profile.basic.ethnicity.value}</span>}
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
                                                {data.target_profile.vibe?.vibe?.value || "Any"}
                                                {data.target_profile.vibe?.vibe?.confidence !== undefined && <span className="text-gray-500 ml-1 text-xs opacity-75">{data.target_profile.vibe.vibe.confidence.toFixed(2)}</span>}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="text-gray-400 block text-xs">Facial Structure</span>
                                            <span className="text-white font-medium">
                                                {data.target_profile.face?.face_shape?.value || "Any"}
                                                {data.target_profile.face?.face_shape?.confidence !== undefined && <span className="text-gray-500 ml-1 text-xs opacity-75">{data.target_profile.face.face_shape.confidence.toFixed(2)}</span>}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="text-gray-400 block text-xs">Demographic</span>
                                            <span className="text-white font-medium">
                                                {data.target_profile.basic?.gender?.value || "Any"} / {data.target_profile.basic?.age_group?.value || "Any"}
                                            </span>
                                        </div>
                                        <div>
                                            <span className="text-gray-400 block text-xs">Style</span>
                                            <span className="text-white font-medium">
                                                {data.target_profile.vibe?.style?.value || "Any"}
                                                {data.target_profile.vibe?.style?.confidence !== undefined && <span className="text-gray-500 ml-1 text-xs opacity-75">{data.target_profile.vibe.style.confidence.toFixed(2)}</span>}
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
