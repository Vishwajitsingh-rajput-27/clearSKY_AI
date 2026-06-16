import { ResearchDashboardContent } from "@/components/inference/research-dashboard-content";
import { PageHeader } from "@/components/shared/page-header";

export default function ResearchDashboardPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Research export"
        title="Research Dashboard"
        description="Generate experiment, benchmark, PDF, CSV, and metrics comparison reports from tracked model evidence."
      />

      <ResearchDashboardContent />
    </div>
  );
}
