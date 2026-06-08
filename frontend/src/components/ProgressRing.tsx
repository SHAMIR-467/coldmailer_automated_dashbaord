type Props = { value: number; max: number; size?: number; color?: string };

export function ProgressRing({ value, max, size = 180, color = "#14b8a6" }: Props) {
  const radius = (size - 18) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = max ? Math.min(1, value / max) : 0;
  const dashOffset = circumference - pct * circumference;

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#1e293b" strokeWidth="12" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          className="transition-all duration-700"
        />
      </svg>
      <div className="-mt-[112px] mb-12 text-center">
        <div className="num font-mono text-2xl font-bold text-white">{value.toLocaleString()}</div>
        <div className="text-xs text-slate-500">/ {max.toLocaleString()}</div>
      </div>
      <div className="text-sm text-slate-400">Daily Email Quota</div>
    </div>
  );
}
