"use client";

import { motion } from "framer-motion";

function getRingColor(value: number) {
  if (value >= 80) return "hsl(var(--success))";
  if (value >= 50) return "hsl(var(--warning))";
  return "hsl(var(--error))";
}

export function ProgressRing({ value, size = 92 }: { value: number; size?: number }) {
  const stroke = 8;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, value));
  const offset = circumference - (clamped / 100) * circumference;
  const ringColor = getRingColor(clamped);

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={radius} stroke="hsl(var(--muted))" strokeWidth={stroke} fill="none" opacity={0.65} />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={ringColor}
          strokeWidth={stroke}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          animate={{ strokeDashoffset: offset }}
          initial={{ strokeDashoffset: circumference }}
          transition={{ type: "spring", stiffness: 120, damping: 18 }}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center text-sm font-semibold text-foreground">{clamped}%</div>
    </div>
  );
}

