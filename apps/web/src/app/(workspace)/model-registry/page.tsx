import { ModelRegistryContent } from "@/components/inference/model-registry-content";
import { PageHeader } from "@/components/shared/page-header";

export default function ModelRegistryPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Experiment tracking"
        title="Model Registry"
        description="Track model versions, datasets, checkpoint status, and best available reconstruction model selection."
      />

      <ModelRegistryContent />
    </div>
  );
}
