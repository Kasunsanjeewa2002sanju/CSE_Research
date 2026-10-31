import React, { useState, useEffect } from 'react';
import { Sparkles, Calendar, Tag, Building2, AlertCircle, RefreshCw, CheckCircle2 } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { useMeta } from '@/context/MetaContext';
import { apiFetch } from '@/api/client';
import { newsItemDetailResponseSchema } from '@/api/zod-schemas';
import type { ScenarioSubmitRequest } from '../types';

export interface ScenarioInputPanelProps {
  onSubmit: (params: ScenarioSubmitRequest) => void;
  isLoading: boolean;
  prefillNewsId?: string | null;
  onClearPrefill?: () => void;
  latestAspiValue?: number;
  latestAspiDate?: string;
  categories?: Array<{ id: string; name: string }>;
  sectors?: Array<{ id: string; name: string; code?: string }>;
}

export function ScenarioInputPanel({
  onSubmit,
  isLoading,
  prefillNewsId,
  onClearPrefill,
  latestAspiValue,
  latestAspiDate,
  categories: propCategories,
  sectors: propSectors,
}: ScenarioInputPanelProps) {
  let metaContext: ReturnType<typeof useMeta> | null = null;
  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    metaContext = useMeta();
  } catch {
    metaContext = null;
  }
  const meta = metaContext?.meta;

  const getTodayColombo = () => {
    try {
      return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Colombo' }).format(new Date());
    } catch {
      return new Date().toISOString().split('T')[0];
    }
  };

  const [headline, setHeadline] = useState('');
  const [description, setDescription] = useState('');
  const [publicationDate, setPublicationDate] = useState(getTodayColombo());
  const [category, setCategory] = useState('political');
  const [sector, setSector] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [prefilledHeadline, setPrefilledHeadline] = useState<string | null>(null);
  const [stepperPhase, setStepperPhase] = useState(1);

  useEffect(() => {
    if (!isLoading) {
      setStepperPhase(1);
      return;
    }
    const t1 = setTimeout(() => setStepperPhase(2), 500);
    const t2 = setTimeout(() => setStepperPhase(3), 1100);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [isLoading]);

  useEffect(() => {
    if (!prefillNewsId) return;
    let isMounted = true;
    apiFetch(`/news/items/${encodeURIComponent(prefillNewsId)}`, newsItemDetailResponseSchema)
      .then((res) => {
        if (!isMounted) return;
        const item = res.item;
        const hl = item.headline || item.title || '';
        setHeadline(hl);
        if (item.description) setDescription(item.description);
        if (item.published_at) setPublicationDate(item.published_at.split('T')[0]);
        if (item.category && item.category !== 'not_relevant') {
          setCategory(item.category);
        }
        setPrefilledHeadline(hl);
      })
      .catch(() => {});
    return () => {
      isMounted = false;
    };
  }, [prefillNewsId]);

  const categories = propCategories || meta?.categories || meta?.news_categories || [
    { id: 'monetary', name: 'Monetary Policy & Central Bank' },
    { id: 'fiscal', name: 'Fiscal Policy, IMF & Sovereign Debt' },
    { id: 'political', name: 'Elections, Parliament & Cabinet' },
    { id: 'trade', name: 'Trade, Exports & Foreign Exchange' },
    { id: 'corporate', name: 'Corporate Earnings & Mergers' },
  ];

  const sectors = propSectors || meta?.sectors || [
    { id: 'banks', name: 'Banking & Financial Services', code: 'BNK' },
    { id: 'capital_goods', name: 'Capital Goods & Conglomerates', code: 'CAP' },
    { id: 'food_bev', name: 'Food, Beverage & Tobacco', code: 'FBT' },
    { id: 'materials', name: 'Materials & Manufacturing', code: 'MAT' },
    { id: 'telecom', name: 'Telecommunication Services', code: 'TEL' },
  ];

  const latestAspi = latestAspiValue ?? meta?.latest_aspi_value ?? 22624.31;
  const asOfDate = latestAspiDate ?? meta?.latest_aspi_date ?? meta?.as_of_date ?? '2025-12-31';

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!headline.trim()) {
      errs.headline = 'Please enter a scenario headline or news title.';
    } else if (headline.trim().length < 5) {
      errs.headline = 'Headline must be at least 5 characters for semantic evaluation.';
    }
    if (!publicationDate) {
      errs.publicationDate = 'Publication date is required.';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    onSubmit({
      headline: headline.trim(),
      description: description.trim(),
      publication_date: publicationDate,
      category,
      sector: sector || undefined,
      current_aspi: latestAspi,
    });
  };

  const handleReset = () => {
    setHeadline('');
    setDescription('');
    setPublicationDate(getTodayColombo());
    setCategory('political');
    setSector('');
    setErrors({});
    setPrefilledHeadline(null);
    onClearPrefill?.();
  };

  return (
    <Card className="border-border bg-surface-white shadow-soft">
      <CardHeader className="flex flex-row items-center justify-between border-b border-border/60 pb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-cobalt/10 text-blue-cobalt">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <CardTitle className="text-base font-semibold text-text-primary">
              Scenario Simulation Input
            </CardTitle>
            <p className="text-xs text-text-muted">
              Configure macroeconomic shock parameters for counterfactual forecasting
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 rounded-md border border-border/80 bg-surface-subtle/60 px-3 py-1 font-mono text-xs">
          <span className="text-text-muted">Latest ASPI Used:</span>
          <span className="font-semibold text-text-primary">{latestAspi.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          <span className="text-[10px] text-text-muted">({asOfDate})</span>
        </div>
      </CardHeader>
      <CardContent className="pt-4">
        {prefilledHeadline && (
          <div className="mb-4 flex items-center justify-between rounded-md border border-blue-soft/40 bg-blue-ice/30 px-3 py-2 text-xs text-blue-navy">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-blue-cobalt" />
              <span><strong>Prefilled from news article:</strong> &ldquo;{prefilledHeadline}&rdquo;</span>
            </div>
            <button type="button" onClick={handleReset} className="text-text-muted hover:text-text-primary text-[11px] underline">
              Clear prefill
            </button>
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="scenario-headline" className="block text-xs font-semibold text-text-primary">
              Headline or Policy Declaration <span className="text-red-coral">*</span>
            </label>
            <input
              id="scenario-headline"
              type="text"
              value={headline}
              onChange={(e) => {
                setHeadline(e.target.value);
                if (errors.headline) setErrors((prev) => ({ ...prev, headline: '' }));
              }}
              placeholder="e.g. Central Bank reduces policy rates by 50 basis points"
              className={`mt-1 w-full rounded-md border px-3 py-2 text-sm text-text-primary placeholder:text-text-muted/60 focus:outline-none focus:ring-1 ${
                errors.headline ? 'border-red-coral focus:ring-red-coral' : 'border-border bg-surface-white focus:border-blue-cobalt focus:ring-blue-cobalt'
              }`}
              disabled={isLoading}
            />
            {errors.headline && (
              <p className="mt-1 flex items-center gap-1 text-[11px] text-red-coral">
                <AlertCircle className="h-3 w-3" /> {errors.headline}
              </p>
            )}
          </div>
          <div>
            <label htmlFor="scenario-description" className="block text-xs font-semibold text-text-primary">
              Context or Policy Description <span className="text-[10px] font-normal text-text-muted">(Optional)</span>
            </label>
            <textarea
              id="scenario-description"
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Provide background context or benchmark conditionalities..."
              className="mt-1 w-full rounded-md border border-border bg-surface-white px-3 py-2 text-xs text-text-primary placeholder:text-text-muted/60 focus:border-blue-cobalt focus:outline-none focus:ring-1 focus:ring-blue-cobalt"
              disabled={isLoading}
            />
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div>
              <label htmlFor="scenario-date" className="flex items-center gap-1 text-xs font-semibold text-text-primary">
                <Calendar className="h-3 w-3 text-text-muted" /> Publication Date
              </label>
              <input
                id="scenario-date"
                type="date"
                value={publicationDate}
                onChange={(e) => setPublicationDate(e.target.value)}
                className="mt-1 w-full rounded-md border border-border bg-surface-white px-2.5 py-1.5 font-mono text-xs text-text-primary focus:border-blue-cobalt focus:outline-none focus:ring-1 focus:ring-blue-cobalt"
                disabled={isLoading}
              />
              <span className="mt-0.5 block text-[10px] text-text-muted">Asia/Colombo (+05:30)</span>
            </div>
            <div>
              <label htmlFor="scenario-category" className="flex items-center gap-1 text-xs font-semibold text-text-primary">
                <Tag className="h-3 w-3 text-text-muted" /> Macro Category
              </label>
              <select
                id="scenario-category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="mt-1 w-full rounded-md border border-border bg-surface-white px-2.5 py-1.5 text-xs text-text-primary focus:border-blue-cobalt focus:outline-none focus:ring-1 focus:ring-blue-cobalt"
                disabled={isLoading}
              >
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="scenario-sector" className="flex items-center gap-1 text-xs font-semibold text-text-primary">
                <Building2 className="h-3 w-3 text-text-muted" /> Target Sector
              </label>
              <select
                id="scenario-sector"
                value={sector}
                onChange={(e) => setSector(e.target.value)}
                className="mt-1 w-full rounded-md border border-border bg-surface-white px-2.5 py-1.5 text-xs text-text-primary focus:border-blue-cobalt focus:outline-none focus:ring-1 focus:ring-blue-cobalt"
                disabled={isLoading}
              >
                <option value="">Whole Market (ASPI Broad Index)</option>
                {sectors.map((s) => (
                  <option key={s.id} value={s.id}>{s.name} ({s.code || s.id})</option>
                ))}
              </select>
            </div>
          </div>
          {isLoading && (
            <div className="rounded-lg border border-blue-soft/60 bg-blue-ice/20 p-3">
              <div className="mb-2 flex items-center gap-2 font-mono text-xs font-semibold text-blue-navy">
                <RefreshCw className="h-3.5 w-3.5 animate-spin text-blue-cobalt" />
                <span>Simulating Counterfactual Scenarios...</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center font-mono text-[11px]">
                <div className={`rounded p-1.5 border transition-all ${stepperPhase >= 1 ? 'border-blue-cobalt bg-surface-white text-blue-navy font-semibold' : 'border-border bg-surface-subtle/50 text-text-muted'}`}>
                  1. Semantic NLP Encoding
                </div>
                <div className={`rounded p-1.5 border transition-all ${stepperPhase >= 2 ? 'border-blue-cobalt bg-surface-white text-blue-navy font-semibold' : 'border-border bg-surface-subtle/50 text-text-muted'}`}>
                  2. Historical Evidence Match
                </div>
                <div className={`rounded p-1.5 border transition-all ${stepperPhase >= 3 ? 'border-blue-cobalt bg-surface-white text-blue-navy font-semibold' : 'border-border bg-surface-subtle/50 text-text-muted'}`}>
                  3. Conformal Forecasting
                </div>
              </div>
            </div>
          )}
          <div className="flex items-center justify-between pt-2">
            <Button type="button" variant="outline" size="sm" onClick={handleReset} disabled={isLoading || (!headline && !description)}>
              Reset Form
            </Button>
            <Button type="submit" size="md" isLoading={isLoading} className="bg-blue-cobalt px-6 font-semibold text-white hover:bg-blue-navy">
              Simulate Counterfactual Scenarios
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
