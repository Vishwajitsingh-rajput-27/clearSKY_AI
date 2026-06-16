import { AccountPanel } from "@/components/settings/account-panel";
import { PageHeader } from "@/components/shared/page-header";

export default function AccountPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="User management"
        title="Account"
        description="Manage projects, history, and storage limits for authenticated public users."
      />

      <AccountPanel />
    </div>
  );
}
