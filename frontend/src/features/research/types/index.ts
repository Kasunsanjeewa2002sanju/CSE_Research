export interface AuditProof {
  dimension: string;
  verdict: 'PASS' | 'FAIL';
  details: string;
  evidence: string;
}

export interface ResearchAuditResponse {
  stage: string;
  audit_date: string;
  proofs: AuditProof[];
  master_index_available: boolean;
}
