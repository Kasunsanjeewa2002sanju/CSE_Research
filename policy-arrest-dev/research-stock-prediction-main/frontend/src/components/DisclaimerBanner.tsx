import React from 'react';
import { AlertTriangle } from 'lucide-react';

export const DisclaimerBanner: React.FC = () => {
  return (
    <div className="bg-amber-50/90 border-b border-amber-200/80 px-4 py-2 text-xs text-amber-900 flex items-center justify-between shadow-xs">
      <div className="flex items-center gap-2">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
        <span>
          <strong className="text-amber-950 font-semibold">Academic Research Platform:</strong> Empirical analysis of political events on the Colombo Stock Exchange. Not financial, investment, or legal advice. Historical price reactions reflect concurrent correlation, not verified monocausality.
        </span>
      </div>
      <span className="hidden md:inline-block text-[11px] text-amber-700 font-mono font-medium">
        CSE Historical Depth: 1985–2025 | 104 Verified Events
      </span>
    </div>
  );
};
