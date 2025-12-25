"use client";

import { useEffect, useState, useMemo, useRef } from "react";
import { motion, AnimatePresence, useSpring, useMotionValue } from "framer-motion";
import {
    Activity,
    Zap,
    Database,
    Cpu,
    Server,
    Lock,
    Cloud,
    CheckCircle2,
    Loader2,
    Camera,
    EyeOff
} from "lucide-react";

// Animated Counter Component
const SPRING_CONFIG = { stiffness: 60, damping: 25, mass: 1 };

function AnimatedCounter({ value, formatter }: { value: number, formatter?: (v: number) => string }) {
    const ref = useRef<HTMLSpanElement>(null);
    const motionValue = useMotionValue(0);
    const springValue = useSpring(motionValue, SPRING_CONFIG);
    const format = formatter || ((v) => Math.round(v).toLocaleString());

    useEffect(() => {
        motionValue.set(value);
    }, [value, motionValue]);

    useEffect(() => {
        return springValue.on("change", (latest) => {
            if (ref.current) {
                ref.current.textContent = format(latest);
            }
        });
    }, [springValue, format]);

    return <span ref={ref}>{format(value)}</span>;
}

// CircularProgress with Determinate Animation
function CircularProgress({ size = 24, strokeWidth = 3, color = "text-yellow-500", label, percent = 0 }: { size?: number, strokeWidth?: number, color?: string, label?: string, percent?: number }) {
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (percent / 100) * circumference;

    return (
        <div className={`relative flex items-center justify-center ${color}`} style={{ width: size, height: size }}>
            {/* Background Ring */}
            <svg className="w-full h-full rotate-[-90deg]">
                <circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="transparent"
                    stroke="currentColor"
                    strokeWidth={strokeWidth}
                    strokeOpacity={0.2}
                />
                {/* Progress Ring (Determinate) */}
                <motion.circle
                    cx={size / 2}
                    cy={size / 2}
                    r={radius}
                    fill="transparent"
                    stroke="currentColor"
                    strokeWidth={strokeWidth}
                    strokeDasharray={circumference}
                    initial={{ strokeDashoffset: circumference }}
                    animate={{ strokeDashoffset: offset }}
                    transition={{ duration: 1.0, ease: "easeOut" }}
                />
            </svg>
            {/* Label Overlay */}
            {label && (
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-[8px] font-bold text-white/90 font-mono tracking-tighter leading-none">{label}</span>
                </div>
            )}
        </div>
    );
}

// Types
interface CostState {
    total_usd: number;
    daily_tokens: {
        high: number;
        stable: number;
        burn: number;
        optimization: number;
    };
    lifetime_tokens: {
        high: number;
        stable: number;
        burn: number;
        optimization: number;
        openai_sum?: number;
    };
    last_reset: string;
}

interface User {
    discord_user_id: string;
    display_name: string | null;
    created_at: number;
    points: number;
    status: "Optimized" | "Pending";
    mode?: string;
    cost_usage?: {
        high: number;
        stable: number;
        burn: number;
        optimization: number;
        total_usd?: number;
    };
    impression?: string | null;
}

interface UserDetail {
    name: string;
    traits: string[];
    history_summary: string;
    impression?: string;
    last_context?: {
        content: string;
        timestamp: string;
        channel: string;
        guild?: string;
    }[];
    last_updated: string;
}

interface HistoryData {
    timeline: {
        date: string;
        high: number;
        stable: number;
        optimization: number;
        burn: number;
        usd: number;
    }[];
    breakdown: {
        [key: string]: {
            total: number;
            [model: string]: number;
        };
    };
}

function HistoryModal({ lane, onClose }: { lane: string, onClose: () => void }) {
    const [history, setHistory] = useState<HistoryData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const res = await fetch("http://localhost:8000/api/dashboard/history");
                if (res.ok) {
                    const data = await res.json();
                    setHistory(data.data);
                }
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, []);

    // Helper: Get data for specific lane
    const getLaneData = (item: any) => {
        if (lane === "usd") return item.usd;
        return item[lane] || 0;
    };

    // Find max for scaling
    const maxVal = history?.timeline.reduce((acc, item) => Math.max(acc, getLaneData(item)), 0) || 1;

    // Color mapping
    const colorMap: Record<string, string> = {
        high: "text-cyan-400 bg-cyan-500",
        stable: "text-green-400 bg-green-500",
        optimization: "text-purple-400 bg-purple-500",
        usd: "text-white bg-neutral-500",
    };
    const theme = colorMap[lane] || colorMap["usd"];
    const [textColor, bgColor] = theme.split(" ");

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" onClick={onClose}>
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="bg-neutral-900 border border-neutral-800 rounded-2xl w-full max-w-4xl max-h-[85vh] overflow-hidden flex flex-col shadow-2xl relative"
                onClick={(e) => e.stopPropagation()}
            >
                <div className="p-6 border-b border-neutral-800 flex justify-between items-center bg-neutral-950/50">
                    <h2 className={`text-2xl font-black uppercase tracking-tight flex items-center gap-3 ${textColor}`}>
                        {lane === "usd" ? "Cost History" : `${lane} Lane History`}
                    </h2>
                    <button onClick={onClose} className="p-2 text-neutral-500 hover:text-white bg-neutral-800 rounded-full">
                        <EyeOff className="w-5 h-5" />
                    </button>
                </div>

                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <Loader2 className={`w-8 h-8 animate-spin ${textColor}`} />
                    </div>
                ) : history ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 h-full overflow-hidden">
                        {/* Chart Area */}
                        <div className="col-span-2 p-6 overflow-y-auto border-r border-neutral-800">
                            <h3 className="text-neutral-500 text-xs font-bold uppercase tracking-wider mb-6">30-Day Activity</h3>

                            <div className="space-y-3">
                                {history.timeline.slice(-30).map((day, i) => {
                                    const val = getLaneData(day);
                                    const percent = (val / maxVal) * 100;
                                    return (
                                        <div key={i} className="flex items-center gap-4 text-xs group">
                                            <span className="w-20 text-right font-mono text-neutral-600">{day.date.slice(5)}</span>
                                            <div className="flex-1 h-6 bg-neutral-800/50 rounded flex items-center overflow-hidden relative">
                                                <motion.div
                                                    initial={{ width: 0 }}
                                                    animate={{ width: `${percent}%` }}
                                                    transition={{ delay: i * 0.02, duration: 0.5, ease: "easeOut" }}
                                                    className={`h-full opacity-80 group-hover:opacity-100 ${bgColor}`}
                                                />
                                                <span className="absolute left-2 text-white font-mono font-bold drop-shadow-md">
                                                    {lane === "usd" ? `$${val.toFixed(2)}` : val.toLocaleString()}
                                                </span>
                                            </div>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>

                        {/* Breakdown Area */}
                        <div className="col-span-1 p-6 bg-neutral-950/30 overflow-y-auto">
                            <h3 className="text-neutral-500 text-xs font-bold uppercase tracking-wider mb-6">Usage Breakdown (Lifetime)</h3>

                            {history.breakdown[lane] ? (
                                <div className="space-y-4">
                                    {Object.entries(history.breakdown[lane])
                                        .filter(([k]) => k !== "total")
                                        .sort(([, a], [, b]) => b - a)
                                        .map(([model, count], i) => (
                                            <div key={i} className="bg-neutral-900 border border-neutral-800 p-3 rounded-lg">
                                                <div className="text-neutral-300 font-medium text-sm mb-1">{model}</div>
                                                <div className={`text-xl font-mono font-bold ${textColor}`}>
                                                    {count.toLocaleString()} <span className="text-xs text-neutral-600">tokens</span>
                                                </div>
                                            </div>
                                        ))}
                                    {Object.keys(history.breakdown[lane]).length <= 1 && (
                                        <div className="text-neutral-600 italic text-sm">No detailed breakdown available.</div>
                                    )}
                                </div>
                            ) : (
                                <div className="text-neutral-500">No data available for this lane.</div>
                            )}
                        </div>
                    </div>
                ) : null}
            </motion.div>
        </div>
    );
}

function UserDetailModal({ userId, onClose }: { userId: string, onClose: () => void }) {
    const [detail, setDetail] = useState<UserDetail | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDetail = async () => {
            try {
                const res = await fetch(`http://localhost:8000/api/dashboard/users/${userId}`);
                if (res.ok) {
                    const data = await res.json();
                    setDetail(data.data);
                }
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };
        fetchDetail();
    }, [userId]);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm" onClick={onClose}>
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="bg-neutral-900 border border-neutral-800 rounded-2xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col shadow-2xl relative"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Close Button */}
                <button onClick={onClose} className="absolute top-4 right-4 p-2 text-neutral-400 hover:text-white bg-black/20 rounded-full z-10">
                    <EyeOff className="w-5 h-5" />
                </button>

                {loading ? (
                    <div className="flex items-center justify-center h-64">
                        <Loader2 className="w-8 h-8 animate-spin text-cyan-500" />
                    </div>
                ) : detail ? (
                    <>
                        {/* Impression Header */}
                        <div className="bg-gradient-to-r from-cyan-950/50 to-purple-950/50 p-8 pt-12 flex flex-col items-center justify-center border-b border-white/5 relative overflow-hidden">
                            <div className="absolute inset-0 bg-[url('/noise.png')] opacity-10 mix-blend-overlay"></div>
                            <h2 className="text-3xl font-black text-white text-center tracking-tight relative z-10">
                                {detail.impression || "分析中..."}
                            </h2>
                            <p className="text-cyan-400/80 font-mono text-sm mt-2 uppercase tracking-widest relative z-10">AI 印象分析</p>
                        </div>

                        {/* Content Scroll - Custom Scrollbar */}
                        <div className="overflow-y-auto p-6 space-y-8 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-neutral-900 [&::-webkit-scrollbar-thumb]:bg-neutral-700 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-neutral-600">

                            {/* Profile Summary */}
                            <div>
                                <h3 className="text-neutral-500 font-bold uppercase tracking-wider text-xs mb-3 flex items-center gap-2">
                                    <Activity className="w-4 h-4" /> 心理プロファイル
                                </h3>
                                <div className="p-4 rounded-xl bg-neutral-800/30 border border-neutral-800 text-neutral-300 leading-relaxed font-serif italic text-lg">
                                    "{detail.history_summary}"
                                </div>
                            </div>

                            {/* Traits */}
                            <div>
                                <h3 className="text-neutral-500 font-bold uppercase tracking-wider text-xs mb-3 flex items-center gap-2">
                                    <Database className="w-4 h-4" /> 検出された特性
                                </h3>
                                <div className="flex flex-wrap gap-2">
                                    {detail.traits.map((t, i) => (
                                        <span key={i} className="px-3 py-1 bg-neutral-800 border border-neutral-700 rounded-full text-neutral-300 text-sm">
                                            #{t}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            {/* Source Context */}
                            {detail.last_context && detail.last_context.length > 0 && (
                                <div>
                                    <h3 className="text-neutral-500 font-bold uppercase tracking-wider text-xs mb-3 flex items-center gap-2">
                                        <Server className="w-4 h-4" /> 分析コンテキスト (直近のトリガー)
                                    </h3>
                                    <div className="space-y-3 bg-neutral-950/50 rounded-xl p-4 border border-neutral-800 max-h-64 overflow-y-auto">
                                        {detail.last_context.map((msg, i) => (
                                            <div key={i} className="border-b border-neutral-800/50 last:border-0 pb-3 last:pb-0">
                                                <div className="flex justify-between text-[10px] text-neutral-500 mb-1 font-mono">
                                                    <span>[{msg.guild || "DM"}] #{msg.channel}</span>
                                                    <span>{new Date(msg.timestamp).toLocaleTimeString()}</span>
                                                </div>
                                                <p className="text-neutral-300 text-sm whitespace-pre-wrap">{msg.content}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="p-8 text-center text-neutral-500">Failed to load details.</div>
                )}
            </motion.div>
        </div>
    );
}

export default function Dashboard() {
    const [usage, setUsage] = useState<CostState | null>(null);
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedUser, setSelectedUser] = useState<string | null>(null);
    const [historyLane, setHistoryLane] = useState<string | null>(null);
    const [screenshotMode, setScreenshotMode] = useState(false);

    // Hardcoded limits
    const LIMIT_HIGH = 100000;
    const LIMIT_STABLE = 2500000;
    const LIMIT_OPT_VISUAL = 2500000;

    const fetchData = async () => {
        try {
            const usageRes = await fetch("http://localhost:8000/api/dashboard/usage");
            if (usageRes.ok) {
                const data = await usageRes.json();
                setUsage(data.data);
            }

            const usersRes = await fetch("http://localhost:8000/api/dashboard/users");
            if (usersRes.ok) {
                const data = await usersRes.json();
                setUsers(data.data);
            }
        } catch (error) {
            console.error("Failed to fetch dashboard data", error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 2000);
        return () => clearInterval(interval);
    }, []);

    // Toggle Screenshot Mode
    const toggleScreenshotMode = () => {
        setScreenshotMode(true);
        setTimeout(() => setScreenshotMode(false), 5000);
    };

    // Sort Users: Pending First, then High Usage
    const sortedUsers = useMemo(() => {
        return [...users].sort((a, b) => {
            // 1. Status: Pending (Processing) comes FIRST
            if (a.status !== b.status) {
                return a.status === "Pending" ? -1 : 1;
            }

            // 2. Secondary Sort: High Usage (Desc)
            const usageA = a.cost_usage?.high || 0;
            const usageB = b.cost_usage?.high || 0;
            return usageB - usageA;
        });
    }, [users]);

    // Privacy Masking
    const maskName = (name: string | null) => screenshotMode ? "User-Protected" : (name || "Unknown");
    const maskID = (id: string) => screenshotMode ? "****-****-****" : id;
    const maskAvatar = (name: string | null) => screenshotMode ? "?" : (name ? name.charAt(0).toUpperCase() : "?");

    // Animation Variants
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.1,
                delayChildren: 0.1
            }
        }
    };

    const itemVariants = {
        hidden: { y: -20, opacity: 0 },
        visible: {
            y: 0,
            opacity: 1,
            transition: { duration: 0.4 }
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-neutral-950 flex items-center justify-center text-neutral-500 font-mono">
                <Loader2 className="w-8 h-8 animate-spin mr-3" />
                <span className="text-xl tracking-widest">ORA SYSTEM INITIALIZING...</span>
            </div>
        );
    }

    return (
        <div className={`min-h-screen bg-neutral-950 text-neutral-200 font-sans w-full p-4 ${screenshotMode ? 'cursor-none select-none' : ''}`}>
            <motion.div
                className="w-full max-w-[2560px] mx-auto space-y-4"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
            >

                {/* Header: Scaled & Tight */}
                <motion.div variants={itemVariants} className="flex justify-between items-end border-b border-neutral-800 pb-4 mb-2">
                    <div>
                        <h1 className="text-5xl font-black text-white tracking-tight mb-1 flex items-center gap-6">
                            <span>ORA <span className="text-cyan-500">SYSTEM</span></span>
                            <span className="text-lg font-bold text-neutral-950 bg-neutral-200 px-3 py-1 rounded border border-neutral-800 whitespace-nowrap self-center mt-2">
                                {screenshotMode ? "PRIVACY SAFE" : "v3.9 FINAL"}
                            </span>
                        </h1>
                        <p className="text-neutral-200 font-medium font-mono text-sm flex items-center gap-2">
                            <Activity className="w-5 h-5" />
                            コスト追跡 & 自律最適化ダッシュボード
                        </p>
                    </div>
                    <div className="text-right">
                        <div className="text-xs text-neutral-600 font-mono mb-1 uppercase tracking-widest">Current Cycle</div>
                        <div className="text-4xl font-mono text-white tracking-widest leading-none">
                            {new Date().toLocaleDateString("ja-JP")}
                        </div>
                    </div>
                </motion.div>

                {/* Global Usage Cards: Large Text / Tight Padding */}
                <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-4 gap-4">

                    {/* High Lane */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        onClick={() => setHistoryLane("high")}
                        className="bg-neutral-900/50 border border-neutral-800/80 rounded-2xl p-4 relative overflow-hidden flex flex-col justify-between group hover:border-cyan-500/30 transition-colors cursor-pointer active:scale-95"
                    >
                        <div className="pointer-events-none absolute top-0 right-0 p-2 opacity-10 font-black text-8xl text-cyan-500 select-none leading-none z-0">HIGH</div>
                        <div className="relative z-10">
                            <div className="flex items-center gap-3 mb-1 text-cyan-400">
                                <Cpu className="w-6 h-6" />
                                <h2 className="text-xl font-bold leading-snug">思考モデル (High)</h2>
                            </div>
                            <p className="text-sm text-neutral-200 font-medium leading-tight">複雑な推論・コーディング</p>
                        </div>
                        <div className="space-y-2 relative z-10 mt-3">
                            <div className="flex justify-between items-baseline text-white">
                                <span className="text-5xl font-mono font-medium tracking-tight leading-none">
                                    <AnimatedCounter value={usage?.daily_tokens.high || 0} />
                                </span>
                                <span className="text-sm text-neutral-600 leading-none">/ {LIMIT_HIGH.toLocaleString()}</span>
                            </div>
                            <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
                                <motion.div
                                    className="h-full bg-cyan-500"
                                    initial={{ width: 0 }}
                                    animate={{ width: `${Math.min(((usage?.daily_tokens.high || 0) / LIMIT_HIGH) * 100, 100)}%` }}
                                    transition={{ type: "spring", ...SPRING_CONFIG }}
                                />
                            </div>
                        </div>
                    </motion.div>

                    {/* Stable Lane */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        onClick={() => setHistoryLane("stable")}
                        className="bg-neutral-900/50 border border-neutral-800/80 rounded-2xl p-4 relative overflow-hidden flex flex-col justify-between group hover:border-green-500/30 transition-colors cursor-pointer active:scale-95"
                    >
                        <div className="pointer-events-none absolute top-0 right-0 p-2 opacity-10 font-black text-8xl text-green-500 select-none leading-none z-0">CHAT</div>
                        <div className="relative z-10">
                            <div className="flex items-center gap-3 mb-1 text-green-400">
                                <Zap className="w-6 h-6" />
                                <h2 className="text-xl font-bold leading-snug">会話モデル (Stable)</h2>
                            </div>
                            <p className="text-sm text-neutral-200 font-medium leading-tight">標準的な会話・応答</p>
                        </div>
                        <div className="space-y-2 relative z-10 mt-3">
                            <div className="flex justify-between items-baseline text-white">
                                <span className="text-5xl font-mono font-medium tracking-tight leading-none">
                                    <AnimatedCounter value={usage?.daily_tokens.stable || 0} />
                                </span>
                                <span className="text-sm text-neutral-600 leading-none">/ {LIMIT_STABLE.toLocaleString()}</span>
                            </div>
                            <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
                                <motion.div
                                    className="h-full bg-green-500"
                                    initial={{ width: 0 }}
                                    animate={{ width: `${Math.min(((usage?.daily_tokens.stable || 0) / LIMIT_STABLE) * 100, 100)}%` }}
                                    transition={{ type: "spring", ...SPRING_CONFIG }}
                                />
                            </div>
                        </div>
                    </motion.div>

                    {/* Optimization Lane */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                        onClick={() => setHistoryLane("optimization")}
                        className="bg-neutral-900/50 border border-neutral-800/80 rounded-2xl p-4 relative overflow-hidden flex flex-col justify-between group hover:border-purple-500/30 transition-colors cursor-pointer active:scale-95"
                    >
                        <div className="pointer-events-none absolute top-0 right-0 p-2 opacity-10 font-black text-8xl text-purple-500 select-none leading-none z-0">MEM</div>
                        <div className="relative z-10">
                            <div className="flex items-center gap-3 mb-1 text-purple-400">
                                <Database className="w-6 h-6" />
                                <h2 className="text-xl font-bold leading-snug">記憶整理 (Opt)</h2>
                            </div>
                            <p className="text-sm text-neutral-200 font-medium leading-tight">バックグラウンド処理</p>
                        </div>
                        <div className="space-y-2 relative z-10 mt-3">
                            <div className="flex justify-between items-baseline text-white">
                                <span className="text-5xl font-mono font-medium tracking-tight leading-none">
                                    <AnimatedCounter value={usage?.daily_tokens.optimization || 0} />
                                </span>
                                <span className="text-sm text-neutral-600 leading-none">/ {LIMIT_OPT_VISUAL.toLocaleString()}</span>
                            </div>
                            <div className="h-2 bg-neutral-800 rounded-full overflow-hidden">
                                <motion.div
                                    className="h-full bg-purple-500"
                                    initial={{ width: 0 }}
                                    animate={{ width: `${Math.min(((usage?.daily_tokens.optimization || 0) / LIMIT_OPT_VISUAL) * 100, 100)}%` }}
                                    transition={{ type: "spring", ...SPRING_CONFIG }}
                                />
                            </div>
                        </div>
                    </motion.div>

                    {/* Total Cost Lane */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4 }}
                        onClick={() => setHistoryLane("usd")}
                        className="bg-neutral-800/30 border border-neutral-800/80 rounded-2xl p-4 relative overflow-hidden flex flex-col justify-center items-center cursor-pointer hover:bg-neutral-800/50 active:scale-95 transition-all"
                    >
                        <div className="pointer-events-none absolute top-0 right-0 p-2 opacity-10 font-black text-8xl text-neutral-600 select-none leading-none z-0">USD</div>
                        <h3 className="text-neutral-500 font-mono text-sm uppercase tracking-widest mb-2 leading-none relative z-10">推定コスト合計 (USD)</h3>
                        <div className="text-6xl font-black text-white font-mono tracking-tighter leading-none my-2 relative z-10">
                            $<AnimatedCounter value={usage?.total_usd || 0} formatter={(v) => v.toFixed(4)} />
                        </div>
                        <p className="text-sm text-neutral-500 leading-none relative z-10">現在のセッション累積</p>
                    </motion.div>

                </motion.div>

                {/* Lifetime Usage Row */}
                <motion.div variants={itemVariants} className="bg-neutral-900 border border-neutral-800/50 rounded-xl p-4 flex items-center justify-between">
                    <span className="text-sm font-semibold text-neutral-400 uppercase tracking-wider whitespace-nowrap mr-8">全期間 (History)</span>
                    {/* Fixed: Grid instead of overflow-x-auto */}
                    <div className="grid grid-cols-2 md:grid-cols-5 w-full gap-8">
                        <div className="flex flex-col">
                            <span className="text-xs text-neutral-600 leading-none mb-1">Stable Chat</span>
                            <span className="text-2xl font-mono text-green-400 leading-none">
                                <AnimatedCounter value={usage?.lifetime_tokens?.stable || 0} />
                            </span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-xs text-neutral-600 leading-none mb-1">High Think</span>
                            <span className="text-2xl font-mono text-cyan-400 leading-none">
                                <AnimatedCounter value={usage?.lifetime_tokens?.high || 0} />
                            </span>
                        </div>
                        <div className="flex flex-col">
                            <span className="text-xs text-neutral-600 leading-none mb-1">Optimization</span>
                            <span className="text-2xl font-mono text-purple-400 leading-none">
                                <AnimatedCounter value={usage?.lifetime_tokens?.optimization || 0} />
                            </span>
                        </div>
                        <div className="flex flex-col border-l border-neutral-800 pl-8">
                            <span className="text-xs text-neutral-500 leading-none mb-1">Total Tokens</span>
                            <span className="text-2xl font-mono text-white leading-none">
                                <AnimatedCounter value={
                                    (usage?.lifetime_tokens?.high || 0) +
                                    (usage?.lifetime_tokens?.stable || 0) +
                                    (usage?.lifetime_tokens?.optimization || 0) +
                                    (usage?.lifetime_tokens?.burn || 0)
                                } />
                            </span>
                        </div>
                        <div className="flex flex-col border-l border-neutral-800 pl-8">
                            <span className="text-xs text-neutral-500 leading-none mb-1">Total USD</span>
                            <span className="text-2xl font-mono text-white leading-none">
                                $<AnimatedCounter value={usage?.total_usd || 0} formatter={(v) => v.toFixed(4)} />
                            </span>
                        </div>
                    </div>
                </motion.div>

                {/* User Grid */}
                <motion.div variants={itemVariants} className="bg-neutral-900 border border-neutral-800 rounded-2xl overflow-hidden shadow-2xl p-4">
                    <div className="flex justify-between items-center mb-4">
                        <div className="flex items-center gap-4">
                            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                                <Server className="w-6 h-6 text-indigo-500" />
                                ユーザー別アクティビティ
                            </h2>
                            <span className="text-xs text-neutral-500 border-l border-neutral-800 pl-4 leading-none">
                                Density: Scaled + Tight (16px)
                            </span>
                        </div>

                        {/* Status Legend */}
                        <div className="flex gap-6">
                            <div className="flex items-center gap-2 text-xs text-neutral-500">
                                <span className="w-2 h-2 rounded-full bg-neutral-500"></span> Queued
                            </div>
                            <div className="flex items-center gap-2 text-xs text-neutral-500">
                                <span className="w-2 h-2 rounded-full bg-cyan-500"></span> Processing
                            </div>
                            <div className="flex items-center gap-2 text-xs text-neutral-500">
                                <span className="w-2 h-2 rounded-full bg-green-500"></span> Optimized
                            </div>
                        </div>
                    </div>

                    <motion.div
                        layout
                        className="grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3 gap-3"
                    >
                        <AnimatePresence mode="popLayout">
                            {sortedUsers.map((user, index) => {
                                // Determine "Processing" vs "Queued"
                                // First Pending user in the list is the "Active Processing" one
                                const isPending = user.status === "Pending";
                                // Check if this is the FIRST pending user in the sorted list
                                const isProcessing = isPending && index === sortedUsers.findIndex(u => u.status === "Pending");
                                const isQueued = isPending && !isProcessing;

                                // Optimization Progress Calculation
                                const optPercent = Math.min(Math.round(((user.cost_usage?.optimization || 0) / 200000) * 100), 99);

                                return (
                                    <motion.div
                                        key={user.discord_user_id}
                                        layout
                                        initial={{ opacity: 0, scale: 0.9 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        transition={{ delay: index * 0.05 }}
                                        onClick={() => setSelectedUser(user.discord_user_id)}
                                        className={`
                                        relative overflow-hidden rounded-xl border p-3 flex items-center gap-4 transition-all cursor-pointer group shadow-lg
                                        ${user.status === "Optimized"
                                                ? "bg-neutral-950/50 border-neutral-800/50 hover:border-green-500/50 hover:bg-neutral-900/80"
                                                : isProcessing
                                                    ? "bg-cyan-950/30 border-cyan-500/60 ring-1 ring-cyan-500/20 shadow-[0_0_15px_rgba(6,182,212,0.15)]" // Processing Style
                                                    : "bg-neutral-900/50 border-neutral-800 text-neutral-500 opacity-60 grayscale-[0.5]" // Queued Style (Dimmed)
                                            }
                                    `}
                                    >
                                        {/* Impression Badge */}
                                        {user.impression && (
                                            <div className="absolute top-0 right-0 px-2 py-0.5 bg-cyan-950/80 text-cyan-400 text-[10px] font-bold border-l border-b border-cyan-500/20 rounded-bl-lg backdrop-blur-sm z-10 group-hover:bg-cyan-900 group-hover:text-cyan-200 transition-colors">
                                                {user.impression}
                                            </div>
                                        )}

                                        {/* Status Bar Indicator */}
                                        <div className={`absolute left-0 top-0 bottom-0 w-1 
                                        ${user.status === "Optimized" ? "bg-green-500"
                                                : isProcessing ? "bg-cyan-400 shadow-[0_0_10px_cyan]"
                                                    : "bg-purple-900" /* Queued */}`}
                                        />

                                        {/* Avatar */}
                                        <div className="flex-shrink-0 ml-1">
                                            <div className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-xl shadow-lg transition-all ${screenshotMode ? "blur-md" : ""
                                                } ${user.status === "Optimized"
                                                    ? "bg-gradient-to-br from-indigo-900 to-neutral-900 text-indigo-400 border border-indigo-500/30"
                                                    : isProcessing
                                                        ? "bg-cyan-950 text-cyan-400 border border-cyan-500/50"
                                                        : "bg-neutral-800 text-neutral-600 border border-neutral-700"
                                                }`}>
                                                {isProcessing ? <Loader2 className="w-5 h-5 animate-spin" /> : maskAvatar(user.display_name)}
                                            </div>
                                        </div>

                                        {/* Main Info */}
                                        <div className="flex-grow min-w-0 grid grid-cols-12 gap-4 items-center">

                                            {/* Identity */}
                                            <div className="col-span-4">
                                                <span className={`font-bold text-xl block truncate leading-tight transition-all 
                                                ${screenshotMode ? "blur-sm opacity-50" : ""}
                                                ${isProcessing ? "text-cyan-100" : "text-white"}
                                            `}>
                                                    {maskName(user.display_name)}
                                                </span>
                                                <span className={`text-sm font-mono truncate block mt-0.5 leading-none transition-all ${screenshotMode ? "blur-sm" : ""} ${isProcessing ? "text-cyan-500/70" : "text-neutral-500"}`}>
                                                    {isProcessing ? "PROCESSING..." : `ID: ${maskID(user.discord_user_id)}`}
                                                </span>
                                            </div>

                                            {/* Mode & Cost */}
                                            <div className="col-span-3 flex flex-col items-start gap-1">
                                                {user.mode?.includes("Private") ? (
                                                    <span className="inline-flex items-center gap-2 px-2 py-0.5 rounded bg-neutral-800 text-neutral-300 border border-neutral-700 text-sm font-bold leading-none">
                                                        <Lock className="w-4 h-4" />
                                                        PvT
                                                    </span>
                                                ) : user.mode?.includes("API") ? (
                                                    <span className="inline-flex items-center gap-2 px-3 py-1 rounded bg-cyan-950/40 text-cyan-400 border border-cyan-500/30 text-xl font-black leading-none tracking-tight">
                                                        <Cloud className="w-5 h-5" />
                                                        API
                                                    </span>
                                                ) : (
                                                    <span className="text-neutral-700 text-xs">-</span>
                                                )}
                                                <div className="flex items-center gap-2 text-xs leading-none ml-0.5">
                                                    <span className="text-neutral-500 font-medium">USD</span>
                                                    <span className="text-white font-mono text-base font-bold">
                                                        $<AnimatedCounter value={user.cost_usage?.total_usd || 0} formatter={(v) => v.toFixed(4)} />
                                                    </span>
                                                </div>
                                            </div>

                                            {/* Stats */}
                                            <div className="col-span-4 flex flex-col gap-1.5">
                                                {/* High Usage */}
                                                <div className="flex justify-between items-center text-xs leading-none">
                                                    <span className="text-neutral-400 font-medium">High</span>
                                                    <span className="text-cyan-200 font-mono text-sm">
                                                        <AnimatedCounter value={user.cost_usage?.high || 0} />
                                                    </span>
                                                </div>
                                                <div className="h-1.5 bg-neutral-800 rounded-full overflow-hidden w-full">
                                                    <motion.div className="h-full bg-cyan-500/50" initial={{ width: 0 }} animate={{ width: `${Math.min(((user.cost_usage?.high || 0) / (LIMIT_HIGH / 10)) * 100, 100)}%` }} transition={{ type: "spring", ...SPRING_CONFIG }} />
                                                </div>

                                                {/* Opt Usage */}
                                                <div className="flex justify-between items-center text-xs leading-none">
                                                    <span className="text-neutral-400 font-medium">Opt</span>
                                                    <span className="text-purple-300 font-mono text-sm">
                                                        <AnimatedCounter value={user.cost_usage?.optimization || 0} />
                                                        <span className="text-purple-300/50 text-[10px] ml-1">/ 200,000</span>
                                                    </span>
                                                </div>
                                                <div className="h-1.5 bg-neutral-800 rounded-full overflow-hidden w-full">
                                                    <motion.div className="h-full bg-purple-500/50" initial={{ width: 0 }} animate={{ width: `${Math.min(((user.cost_usage?.optimization || 0) / 200000) * 100, 100)}%` }} transition={{ type: "spring", ...SPRING_CONFIG }} />
                                                </div>
                                            </div>

                                            {/* Status Icon */}
                                            <div className="col-span-1 flex justify-end">
                                                {user.status === "Optimized" ? (
                                                    <div className="text-green-500">
                                                        <CheckCircle2 className="w-6 h-6" />
                                                    </div>
                                                ) : isProcessing ? (
                                                    <CircularProgress
                                                        size={32}
                                                        strokeWidth={3}
                                                        color="text-cyan-400"
                                                        label={`${optPercent}%`}
                                                        percent={optPercent}
                                                    />
                                                ) : (
                                                    <div className="w-6 h-6 rounded-full border-2 border-neutral-700 border-dashed animate-spin-slow opacity-20" />
                                                )}
                                            </div>

                                        </div>
                                    </motion.div>
                                )
                            })}
                        </AnimatePresence>
                    </motion.div>
                </motion.div>
            </motion.div >

            {/* Float Button */}
            {
                !screenshotMode && (
                    <button
                        onClick={toggleScreenshotMode}
                        className="fixed bottom-8 right-8 bg-black text-white p-4 rounded-full shadow-2xl hover:scale-110 active:scale-95 transition-transform z-50 group flex items-center justify-center gap-2 border border-neutral-700"
                    >
                        {screenshotMode ? <EyeOff className="w-6 h-6" /> : <Camera className="w-6 h-6" />}

                        <span className="absolute right-full mr-4 bg-black text-white text-sm px-3 py-1.5 rounded border border-neutral-800 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none font-medium">
                            Privacy Shot
                        </span>
                    </button>
                )
            }
            {/* Modal */}
            <AnimatePresence>
                {selectedUser && (
                    <UserDetailModal userId={selectedUser} onClose={() => setSelectedUser(null)} />
                )}
                {historyLane && (
                    <HistoryModal lane={historyLane} onClose={() => setHistoryLane(null)} />
                )}
            </AnimatePresence>
        </div >
    );
}
