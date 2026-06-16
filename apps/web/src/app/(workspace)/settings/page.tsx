import { SettingsForm } from "@/components/settings/settings-form";
import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Configuration"
        title="Settings"
        description="Manage local workspace preferences and review environment-level deployment settings."
      />
      <SettingsForm />
      <Card>
        <CardHeader>
          <CardTitle>Production environment</CardTitle>
          <CardDescription>Values below are configured in Render, Vercel, Neon, and storage providers.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {[
            ["Frontend", "Vercel"],
            ["Backend", "Render FastAPI"],
            ["Database", "Neon PostgreSQL"],
            ["Preview storage", "Cloudinary"]
          ].map(([label, value], index, rows) => (
            <div key={label}>
              <div className="flex items-center justify-between gap-4">
                <span className="text-muted-foreground">{label}</span>
                <span className="font-medium">{value}</span>
              </div>
              {index < rows.length - 1 ? <Separator className="mt-3" /> : null}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
