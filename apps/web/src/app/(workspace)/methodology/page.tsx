import { CheckCircle2 } from "lucide-react";
import { PageHeader } from "@/components/shared/page-header";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { methodologySteps } from "@/lib/mock-data";

export default function MethodologyPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Research design"
        title="Methodology"
        description="Document the operational flow from ingest to cloud-free output, keeping scientific and visual products separate."
      />

      <Alert>
        <AlertTitle>Architecture principle</AlertTitle>
        <AlertDescription>
          clearSKY AI prioritizes geospatial validity, spectral preservation, and auditable uncertainty
          before visual polish.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle>Frozen workflow</CardTitle>
          <CardDescription>Module sequence used by engineering and research teams.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {methodologySteps.map((step, index) => (
            <div key={step}>
              <div className="flex gap-3">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">Step {index + 1}</p>
                  <p className="text-sm text-muted-foreground">{step}</p>
                </div>
              </div>
              {index < methodologySteps.length - 1 ? <Separator className="mt-4" /> : null}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

