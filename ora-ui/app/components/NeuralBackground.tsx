"use client";

import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

interface NeuralBackgroundProps {
    intensity?: number; // 0.0 to 1.0 (or higher for boost)
    frozen?: boolean;   // If true, stops all movement
}

interface Node {
    x: number;
    y: number;
    vx: number;
    vy: number;
    radius: number;
    phase: number; // For pulsing
    layerIndex: number; // Layer from 0 to N
    targets: number[]; // Indices of connected nodes in the complete array
}

interface Pulse {
    x: number;
    y: number;
    targetX: number;
    targetY: number;
    progress: number; // 0 to 1
    speed: number;
    color: string;
}

const NeuralBackground: React.FC<NeuralBackgroundProps & { className?: string }> = ({ intensity = 0, frozen = false, className }) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    // Config - MLP Structure
    const LAYERS = [12, 16, 16, 10];
    const BOOST_SPEED_MULTIPLIER = 5.0;

    // Refs for animation state
    const nodesRef = useRef<Node[]>([]);
    const pulsesRef = useRef<Pulse[]>([]);
    const animationRef = useRef<number>(0);
    const dimensionsRef = useRef({ w: 0, h: 0 });

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Initialize Nodes in Layers
        const initNodes = () => {
            const { width, height } = canvas.getBoundingClientRect();
            // Force high resolution (at least 2x)
            const dpr = Math.max(window.devicePixelRatio || 1, 2);

            canvas.width = width * dpr;
            canvas.height = height * dpr;
            ctx.scale(dpr, dpr);
            dimensionsRef.current = { w: width, h: height };

            const newNodes: Node[] = [];

            // Layout params
            const xPadding = width * 0.1;
            const workingWidth = width - (xPadding * 2);

            // 1. Create Nodes First
            let currentNodeIndex = 0;
            const layerStartIndices: number[] = [];

            LAYERS.forEach((nodeCount, layerIndex) => {
                layerStartIndices.push(currentNodeIndex);
                const layerX = xPadding + (workingWidth / (LAYERS.length - 1)) * layerIndex;
                const workingHeight = height * 0.8;
                const yStart = (height - workingHeight) / 2;
                const yStep = workingHeight / (nodeCount + 1);

                for (let i = 0; i < nodeCount; i++) {
                    newNodes.push({
                        x: layerX,
                        y: yStart + (yStep * (i + 1)),
                        vx: 0,
                        vy: 0,
                        radius: (layerIndex === 0 || layerIndex === LAYERS.length - 1) ? 3.5 : 2.5, // Larger nodes to stand out
                        phase: Math.random() * Math.PI * 2,
                        layerIndex: layerIndex,
                        targets: []
                    });
                    currentNodeIndex++;
                }
            });

            // 2. Create Sparse Connections (Pre-calculated)
            newNodes.forEach((node) => {
                if (node.layerIndex < LAYERS.length - 1) {
                    // Find index range of next layer
                    const nextLayerIndex = node.layerIndex + 1;
                    const startIdx = layerStartIndices[nextLayerIndex];
                    const count = LAYERS[nextLayerIndex];

                    for (let i = 0; i < count; i++) {
                        // SPARSITY: Connect to random 35% of nodes
                        if (Math.random() < 0.35) {
                            node.targets.push(startIdx + i);
                        }
                    }
                    // Fallback: Ensure at least one connection if none added (avoid orphan nodes)
                    if (node.targets.length === 0) {
                        const randomNext = startIdx + Math.floor(Math.random() * count);
                        node.targets.push(randomNext);
                    }
                }
            });

            nodesRef.current = newNodes;
        };

        initNodes();

        const render = () => {
            const { w, h } = dimensionsRef.current;
            ctx.clearRect(0, 0, w, h);

            const speedMult = frozen ? 0 : (1 + (intensity * BOOST_SPEED_MULTIPLIER));
            // Very faint background lines to reduce visual noise
            const connectionAlpha = 0.03 + (intensity * 0.02);

            ctx.lineWidth = 0.5; // Thinner lines for crispness

            nodesRef.current.forEach((nodeA) => {
                // Draw Connections using pre-calculated targets
                nodeA.targets.forEach(targetIdx => {
                    const nodeB = nodesRef.current[targetIdx];
                    if (!nodeB) return;

                    ctx.beginPath();
                    ctx.moveTo(nodeA.x, nodeA.y);
                    ctx.lineTo(nodeB.x, nodeB.y);
                    ctx.strokeStyle = `rgba(120, 220, 255, ${connectionAlpha})`;
                    ctx.stroke();

                    // Fire Pulse Logic
                    if (!frozen && Math.random() < (0.0003 + (intensity * 0.001))) {
                        pulsesRef.current.push({
                            x: nodeA.x,
                            y: nodeA.y,
                            targetX: nodeB.x,
                            targetY: nodeB.y,
                            progress: 0,
                            speed: 0.01 + (Math.random() * 0.01) + (intensity * 0.01),
                            color: intensity > 0.5 ? '#a855f7' : '#22d3ee'
                        });
                    }
                });

                // Draw Node
                ctx.beginPath();
                ctx.arc(nodeA.x, nodeA.y, nodeA.radius, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(255, 255, 255, 0.9)`;
                ctx.fill();
            });

            // Update & Draw Pulses
            for (let i = pulsesRef.current.length - 1; i >= 0; i--) {
                const pulse = pulsesRef.current[i];
                if (!frozen) pulse.progress += pulse.speed * speedMult;

                if (pulse.progress >= 1) {
                    pulsesRef.current.splice(i, 1);
                    continue;
                }

                const currX = pulse.x + (pulse.targetX - pulse.x) * pulse.progress;
                const currY = pulse.y + (pulse.targetY - pulse.y) * pulse.progress;

                ctx.beginPath();
                ctx.arc(currX, currY, 2.5, 0, Math.PI * 2); // Larger pulse
                ctx.fillStyle = pulse.color;
                ctx.fill();
            }

            animationRef.current = requestAnimationFrame(render);
        };

        render();

        const handleResize = () => initNodes();
        window.addEventListener('resize', handleResize);
        return () => {
            cancelAnimationFrame(animationRef.current);
            window.removeEventListener('resize', handleResize);
        };
    }, [intensity, frozen]);

    return (
        <motion.canvas
            ref={canvasRef}
            className={`absolute inset-0 z-0 pointer-events-none bg-black/40 ${className || ''}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 2 }}
            style={{ width: '100%', height: '100%' }}
        />
    );
};

export default NeuralBackground;
