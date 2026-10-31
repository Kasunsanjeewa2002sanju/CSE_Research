import { useState } from 'react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import {
  Trophy,
  Calendar,
  Layers,
  Database,
  CheckCircle2,
  AlertTriangle,
  FileText,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Cpu,
} from 'lucide-react';
import type { FinalModelResponse } from '../types';

export interface FinalModelCardProps {
  finalModel: FinalModelResponse;
}

export function FinalModelCard({ finalModel }: FinalModelCardProps) {
  const [activeDocTab, setActiveDocTab] = useState<'card' | 'trace'>('card');
  const [showFullMarkdown, setShowFullMarkdown] = useState(false);

  return (
    <div className="space-y-6">
      {/* 1. Champion Model Hero Banner */}
      <div className="p-6 bg-gradient-to-r from-blue-900 via-blue-800 to-indigo-900 rounded-xl text-white shadow-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-400 text-amber-950 shadow-sm">
                <Trophy className="w-3.5 h-3.5" />
                Selected Production Champion
              </span>
              <Badge variant="outline" className="text-blue-100 border-blue-400/50">
                {finalModel.family.toUpperCase()}
              </Badge>
              <Badge variant="outline" className="text-blue-100 border-blue-400/50">
                v{finalModel.version}
              </Badge>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
              {finalModel.model_name}
            </h1>
            <p className="text-sm text-blue-200 font-mono">
              ID: {finalModel.model_id} &bull; Architecture: {finalModel.architecture}
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            <div className="p-3 bg-blue-950/60 rounded-lg border border-blue-700/50 text-right">
              <div className="text-xs text-blue-300 font-medium">Selection Verdict</div>
              <div className="text-sm font-semibold text-emerald-300 mt-0.5">
                {finalModel.selection_verdict}
              </div>
            </div>
          </div>
        </div>

        {/* Quick Spec Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-5 border-t border-blue-700/60 text-xs">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-blue-300 flex-shrink-0" />
            <div>
              <span className="text-blue-300 block">Data Range</span>
              <span className="font-semibold">{finalModel.training_data_range.join(' to ')}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-blue-300 flex-shrink-0" />
            <div>
              <span className="text-blue-300 block">Training Samples</span>
              <span className="font-semibold">{finalModel.n_training_samples.toLocaleString()} trading days</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-300 flex-shrink-0" />
            <div>
              <span className="text-blue-300 block">Feature Set</span>
              <span className="font-semibold">{finalModel.n_features} features (Set C)</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-blue-300 flex-shrink-0" />
            <div>
              <span className="text-blue-300 block">License & Release</span>
              <span className="font-semibold">{finalModel.license} &bull; {finalModel.release_date}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Key Metrics & Pre-registered Decision Trace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Empirical Performance Metrics */}
        <div className="bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <Trophy className="w-4 h-4 text-amber-500" />
              Empirical Performance
            </h2>
            <span className="text-xs text-slate-500">Cross-Phase Mean</span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {Object.entries(finalModel.empirical_metrics).map(([key, val]) => (
              <div key={key} className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-lg border border-slate-100 dark:border-slate-700">
                <span className="text-xs text-slate-500 dark:text-slate-400 uppercase tracking-wider block">
                  {key.replace(/_/g, ' ')}
                </span>
                <span className="text-lg font-bold text-slate-800 dark:text-slate-200 font-mono mt-0.5 block">
                  {typeof val === 'number' ? (val < 1 && val > -1 ? val.toFixed(4) : val.toLocaleString()) : String(val)}
                </span>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
            <h3 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
              Top Predictive Features (Gini Importance)
            </h3>
            <div className="space-y-1.5">
              {finalModel.top_features.map((feat: { feature?: string; name?: string; importance?: number | string }, idx: number) => (
                <div key={idx} className="flex items-center justify-between text-xs py-1 px-2 rounded bg-slate-50 dark:bg-slate-800">
                  <span className="font-mono text-slate-700 dark:text-slate-300 font-medium">
                    {feat.feature || feat.name}
                  </span>
                  <span className="font-mono text-blue-600 dark:text-blue-400 font-semibold">
                    {typeof feat.importance === 'number' ? feat.importance.toFixed(3) : feat.importance}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Pre-Registered Selection Decision Trace */}
        <div className="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400" />
              Pre-Registered Decision Trace
            </h2>
            <Badge variant="outline" className="text-xs font-medium border-teal-500 text-teal-700 dark:text-teal-300">
              Protocol Locked
            </Badge>
          </div>

          <p className="text-xs text-slate-600 dark:text-slate-400">
            The winning model was selected strictly following the pre-registered 5-tier hierarchical decision rule documented in Stage 9:
          </p>

          <div className="space-y-3">
            {finalModel.selection_hierarchy.map((step, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3 rounded-lg border border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40"
              >
                <div className="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/60 text-blue-700 dark:text-blue-300 font-bold text-xs flex items-center justify-center flex-shrink-0 mt-0.5">
                  {idx + 1}
                </div>
                <div className="text-xs space-y-0.5 flex-1">
                  <span className="font-semibold text-slate-800 dark:text-slate-200">
                    {step}
                  </span>
                </div>
                <CheckCircle2 className="w-4 h-4 text-teal-600 dark:text-teal-400 flex-shrink-0 mt-0.5" />
              </div>
            ))}
          </div>

          {/* Training Hyperparameters */}
          <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
            <h3 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2">
              Validated Hyperparameters
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {Object.entries(finalModel.hyperparameters).map(([hp, val]) => (
                <div key={hp} className="p-2 rounded bg-slate-50 dark:bg-slate-800 text-xs font-mono">
                  <span className="text-slate-500 block text-[10px] truncate">{hp}</span>
                  <span className="font-bold text-slate-800 dark:text-slate-200">{String(val)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* 3. Limitations and Operational Governance */}
      <div className="bg-amber-50/60 dark:bg-amber-950/20 rounded-xl p-5 border border-amber-200 dark:border-amber-900/40 shadow-sm space-y-3">
        <div className="flex items-center gap-2 text-amber-800 dark:text-amber-300 font-semibold text-sm">
          <ShieldAlert className="w-4 h-4" />
          Pre-Registered Limitations & Operational Boundaries
        </div>
        <p className="text-xs text-amber-900/80 dark:text-amber-300/80">
          In compliance with research integrity guidelines, the following analytical constraints govern the production deployment of this model:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
          {finalModel.limitations.map((limit, idx) => (
            <div
              key={idx}
              className="flex items-start gap-2.5 p-3 rounded-lg bg-white/80 dark:bg-slate-900/80 border border-amber-200/80 dark:border-amber-900/50 text-xs text-slate-700 dark:text-slate-300"
            >
              <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
              <span>{limit}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 4. Complete Model Documentation & Decision Trace Viewer */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              Official Model Documentation & Audit Log
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex rounded-md shadow-sm">
              <Button
                variant={activeDocTab === 'card' ? 'primary' : 'outline'}
                size="sm"
                className="text-xs"
                onClick={() => setActiveDocTab('card')}
              >
                Model Card (Markdown)
              </Button>
              <Button
                variant={activeDocTab === 'trace' ? 'primary' : 'outline'}
                size="sm"
                className="text-xs ml-1"
                onClick={() => setActiveDocTab('trace')}
              >
                Decision Trace (Markdown)
              </Button>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-xs"
              onClick={() => setShowFullMarkdown(!showFullMarkdown)}
            >
              {showFullMarkdown ? <ChevronUp className="w-3.5 h-3.5 mr-1" /> : <ChevronDown className="w-3.5 h-3.5 mr-1" />}
              {showFullMarkdown ? 'Collapse' : 'Expand'}
            </Button>
          </div>
        </div>

        <div className={`p-4 transition-all ${showFullMarkdown ? 'max-h-none' : 'max-h-80 overflow-y-auto'}`}>
          <pre className="text-xs font-mono text-slate-700 dark:text-slate-300 whitespace-pre-wrap leading-relaxed bg-slate-50 dark:bg-slate-950 p-4 rounded-lg border border-slate-100 dark:border-slate-800">
            {activeDocTab === 'card' ? finalModel.model_card_markdown : finalModel.decision_trace_markdown}
          </pre>
        </div>
      </div>
    </div>
  );
}
