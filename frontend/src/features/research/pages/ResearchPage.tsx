import { RouteSkeleton } from '@/components/layout/RouteSkeleton';

export default function ResearchPage() {
  return (
    <RouteSkeleton
      title="Research Paper, LaTeX Bundle & External Audit"
      description="Skeptical reviewer audit suite verifying zero lookahead, walk-forward splits, machine reproducibility, and publication LaTeX artifacts."
      breadcrumbs={[{ label: 'Home', to: '/' }, { label: 'Research & Audit' }]}
      stageScheduled="STAGE F9"
      stageName="Research Paper, Replication & Audit"
      dataPointsDescription="/api/v1/research/audit, /api/v1/research/replication-bundle"
    />
  );
}
