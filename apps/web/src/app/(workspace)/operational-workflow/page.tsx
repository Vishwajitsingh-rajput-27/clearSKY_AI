import { OperationalWorkflowContent } from "@/components/inference/operational-workflow-content";
import { PageHeader } from "@/components/shared/page-header";

export default function OperationalWorkflowPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Innovation layer"
        title="Operational Workflow"
        description="Explainable reconstruction, confidence scoring, time-series comparison, and AI recommendations."
      />

      <OperationalWorkflowContent />
    </div>
  );
}
