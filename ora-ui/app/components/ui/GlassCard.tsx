import { motion } from "framer-motion";
import { ReactNode } from "react";

interface GlassCardProps {
    children: ReactNode;
    className?: string;
    title?: string;
}

export default function GlassCard({ children, className = "", title }: GlassCardProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className={`glass rounded-2xl p-6 relative overflow-hidden ${className}`}
        >
            {/* Glossy Gradient Overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />

            {title && (
                <h3 className="text-lg font-semibold mb-4 text-white/90 border-b border-white/10 pb-2 flex items-center gap-2">
                    {title}
                </h3>
            )}

            <div className="relative z-10">
                {children}
            </div>
        </motion.div>
    );
}
