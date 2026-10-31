import { useMemo } from 'react';
import type { EChartsOption } from 'echarts';
import { EChart } from '@/components/charts/EChart';
import { Badge } from '@/components/ui/Badge';
import { Download, FileCode } from 'lucide-react';
import type { ModelDetailResponse } from '../types';

export interface ModelDetailDiagnosticsProps {
  detail: ModelDetailResponse;
}

export function ModelDetailDiagnostics({ detail }: ModelDetailDiagnosticsProps) {
  // 1. Residual Histogram Option
  const histOption = useMemo<EChartsOption>(() => {
    const bins = detail.residuals.histogram;
    const categories = bins.map((b) => `${b.bin_start.toFixed(3)} to ${b.bin_end.toFixed(3)}`);
    const counts = bins.map((b) => b.count);

    return {
      tooltip: { trigger: 'axis' },
      grid: { left: '8%', right: '4%', bottom: '20%', top: '10%' },
      xAxis: { type: 'category', data: categories, axisLabel: { rotate: 30, fontSize: 9 } },
      yAxis: { type: 'value', name: 'Count', splitLine: { lineStyle: { type: 'dashed' } } },
      series: [
        {
          name: 'Residuals',
          type: 'bar',
          data: counts,
          itemStyle: { color: '#0A2A66' },
        },
      ],
    };
  }, [detail]);

  // 2. Residual QQ Plot Option
  const qqOption = useMemo<EChartsOption>(() => {
    const points = detail.residuals.qq_plot.map((p) => [p.theoretical_quantile, p.sample_quantile]);
    return {
      tooltip: {
        trigger: 'item',
        formatter: (params: unknown) => {
          const p = params as { value: [number, number] };
          return `Theoretical: ${p.value[0]}<br/>Sample: ${p.value[1]}`;
        },
      },
      grid: { left: '10%', right: '6%', bottom: '12%', top: '10%' },
      xAxis: { type: 'value', name: 'Theoretical Normal Quantiles', splitLine: { lineStyle: { type: 'dashed' } } },
      yAxis: { type: 'value', name: 'Sample Standardized Quantiles', splitLine: { lineStyle: { type: 'dashed' } } },
      series: [
        {
          type: 'scatter',
          symbolSize: 7,
          data: points,
          itemStyle: { color: '#0095B3' },
          markLine: {
            symbol: 'none',
            data: [[{ coord: [-3, -3] }, { coord: [3, 3] }]],
            lineStyle: { color: '#F59E0B', type: 'dashed', width: 2 },
          },
        },
      ],
    };
  }, [detail]);

  // 3. Feature Importance Option (for trees) or Training Curve (for deep)
  const isDeep = detail.training_curves && detail.training_curves.length > 0;
  const treeOrDeepOption = useMemo<EChartsOption>(() => {
    if (isDeep) {
      const iters = detail.training_curves.map((c) => c.iteration);
      const trainL = detail.training_curves.map((c) => c.train_loss);
      const valL = detail.training_curves.map((c) => c.val_loss);
      return {
        tooltip: { trigger: 'axis' },
        legend: { data: ['Train Loss', 'Validation Loss'], top: '2%' },
        grid: { left: '8%', right: '4%', bottom: '12%', top: '14%' },
        xAxis: { type: 'category', data: iters, name: 'Epoch / Iteration' },
        yAxis: { type: 'value', name: 'Loss', splitLine: { lineStyle: { type: 'dashed' } } },
        series: [
          { name: 'Train Loss', type: 'line', data: trainL, itemStyle: { color: '#0A2A66' } },
          { name: 'Validation Loss', type: 'line', data: valL, itemStyle: { color: '#0095B3' } },
        ],
      };
    }

    const feats = detail.feature_importance.slice(0, 10).reverse();
    return {
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '26%', right: '8%', bottom: '10%', top: '5%' },
      xAxis: { type: 'value', name: 'Importance (%)', axisLabel: { formatter: '{value}%' } },
      yAxis: { type: 'category', data: feats.map((f) => f.feature), axisLabel: { fontSize: 10 } },
      series: [
        {
          name: 'Importance',
          type: 'bar',
          data: feats.map((f) => f.importance),
          itemStyle: { color: '#3563C1' },
          label: { show: true, position: 'right', formatter: '{c}%', fontSize: 10 },
        },
      ],
    };
  }, [detail, isDeep]);

  const cm = detail.confusion_matrix;

  return (
    <div className="space-y-6">
      {/* Residual Diagnostics Row (Histogram & QQ Plot) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Histogram Card */}
        <div className="bg-card p-5 rounded-lg border border-border shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="font-heading text-sm font-bold text-foreground">
              Residual Error Distribution
            </h3>
            <Badge variant="outline" className="font-mono text-[10px]">
              Ljung-Box: p = {detail.residuals.lb_pval_lag5} ({detail.residuals.is_white_noise ? 'White Noise' : 'Autocorrelated'})
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground font-sans">
            Mean: {detail.residuals.mean.toFixed(5)} | SD: {detail.residuals.std.toFixed(4)} | Skew: {detail.residuals.skewness}
          </p>
          <div className="h-[250px] w-full">
            <EChart option={histOption} height="100%" />
          </div>
        </div>

        {/* QQ Plot Card */}
        <div className="bg-card p-5 rounded-lg border border-border shadow-sm space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="font-heading text-sm font-bold text-foreground">
              Quantile-Quantile (QQ) Normal Residual Fit
            </h3>
            <Badge variant="outline" className="font-mono text-[10px]">
              Kurtosis: {detail.residuals.kurtosis}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground font-sans">
            Sample quantiles plotted against standard normal theoretical distribution line.
          </p>
          <div className="h-[250px] w-full">
            <EChart option={qqOption} height="100%" />
          </div>
        </div>
      </div>

      {/* Feature Importance / Training Curves & Confusion Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Feature Importance / Training Curves */}
        <div className="bg-card p-5 rounded-lg border border-border shadow-sm lg:col-span-2 space-y-2">
          <h3 className="font-heading text-sm font-bold text-foreground">
            {isDeep ? 'Deep Model Training & Validation Loss Curves' : 'Top Feature Importances (Tree Split Gain)'}
          </h3>
          <p className="text-xs text-muted-foreground font-sans">
            {isDeep ? 'Tracking convergence across iterations without overfitting.' : 'Gini / split gain attribution across Feature Set C indicators.'}
          </p>
          <div className="h-[280px] w-full">
            <EChart option={treeOrDeepOption} height="100%" />
          </div>
        </div>

        {/* Direction Confusion Matrix Card */}
        <div className="bg-card p-5 rounded-lg border border-border shadow-sm space-y-3">
          <h3 className="font-heading text-sm font-bold text-foreground">
            Directional Classification Matrix
          </h3>
          <p className="text-xs text-muted-foreground font-sans">
            Sign prediction: True Positive (Up), True Negative (Down).
          </p>

          <div className="grid grid-cols-2 gap-2 text-center font-mono text-xs">
            <div className="bg-primary/10 border border-primary/20 p-2.5 rounded">
              <div className="text-[10px] text-muted-foreground uppercase">True Positive (Up)</div>
              <div className="text-lg font-bold text-primary mt-0.5">{cm.true_positive}</div>
            </div>
            <div className="bg-muted/40 border border-border p-2.5 rounded">
              <div className="text-[10px] text-muted-foreground uppercase">False Positive</div>
              <div className="text-lg font-bold text-foreground mt-0.5">{cm.false_positive}</div>
            </div>
            <div className="bg-muted/40 border border-border p-2.5 rounded">
              <div className="text-[10px] text-muted-foreground uppercase">False Negative</div>
              <div className="text-lg font-bold text-foreground mt-0.5">{cm.false_negative}</div>
            </div>
            <div className="bg-primary/10 border border-primary/20 p-2.5 rounded">
              <div className="text-[10px] text-muted-foreground uppercase">True Negative (Down)</div>
              <div className="text-lg font-bold text-primary mt-0.5">{cm.true_negative}</div>
            </div>
          </div>

          <div className="space-y-1.5 text-xs font-mono border-t border-border/60 pt-3">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Accuracy:</span>
              <span className="font-semibold text-foreground">{cm.accuracy.toFixed(2)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Precision:</span>
              <span className="font-semibold text-foreground">{cm.precision.toFixed(2)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Recall (Sensitivity):</span>
              <span className="font-semibold text-foreground">{cm.recall.toFixed(2)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">F1-Score:</span>
              <span className="font-semibold text-foreground">{cm.f1_score.toFixed(2)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Matthews Corr (MCC):</span>
              <span className="font-semibold text-foreground">{cm.mcc.toFixed(4)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Model Artifacts Download Card */}
      <div className="bg-card p-5 rounded-lg border border-border shadow-sm space-y-3">
        <h3 className="font-heading text-sm font-bold text-foreground">
          Downloadable Trained Checkpoint Artifacts
        </h3>
        <p className="text-xs text-muted-foreground font-sans">
          Cryptographically hashed model weights, serialized preprocessing pipelines, and feature metadata schemas.
        </p>

        <div className="overflow-x-auto rounded border border-border">
          <table className="w-full text-xs font-mono text-left" aria-label="Model artifacts download table">
            <thead className="bg-muted/50 border-b border-border text-[10px] uppercase text-muted-foreground">
              <tr>
                <th className="p-2.5">Artifact Name</th>
                <th className="p-2.5">Size</th>
                <th className="p-2.5">SHA256 Hash</th>
                <th className="p-2.5">Updated</th>
                <th className="p-2.5 text-right">Download</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {detail.artifacts.map((art) => (
                <tr key={art.name} className="hover:bg-muted/30">
                  <td className="p-2.5 font-semibold flex items-center gap-1.5">
                    <FileCode className="w-3.5 h-3.5 text-primary" /> {art.name}
                  </td>
                  <td className="p-2.5 text-muted-foreground">{(art.file_size_bytes / 1024).toFixed(1)} KB</td>
                  <td className="p-2.5 font-mono text-[10px] text-muted-foreground truncate max-w-[200px]" title={art.sha256}>
                    {art.sha256.slice(0, 16)}...
                  </td>
                  <td className="p-2.5 text-muted-foreground">{art.updated_at.slice(0, 10)}</td>
                  <td className="p-2.5 text-right">
                    <a
                      href={art.download_url}
                      download
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-primary/10 text-primary hover:bg-primary/20 text-xs font-sans font-medium transition-colors"
                    >
                      <Download className="w-3 h-3" /> Get File
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
