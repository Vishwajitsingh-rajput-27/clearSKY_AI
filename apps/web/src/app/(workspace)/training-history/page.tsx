import { TrainingHistoryContent } from "@/components/inference/training-history-content";
import { PageHeader } from "@/components/shared/page-header";

export default function TrainingHistoryPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Model lineage"
        title="Training History"
        description="Review experiment runs, metrics history, dataset versions, and checkpoint lineage."
      />

      <TrainingHistoryContent />
    </div>
  );
}
