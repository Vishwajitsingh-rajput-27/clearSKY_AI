import Link from "next/link";
import { ArrowRight, BarChart3, Cloud, Database, ShieldCheck } from "lucide-react";
import { DemoModeCard } from "@/components/demo/demo-mode-card";
import { DemoRunButton } from "@/components/demo/demo-run-button";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

const capabilities = [
  {
    title: "Sensor-aware workflow",
    description: "LISS-IV scene validation, masks, reconstruction, and QA in one console.",
    icon: Database
  },
  {
    title: "Scientific guardrails",
    description: "Spectral preservation and uncertainty are treated as first-class outputs.",
    icon: ShieldCheck
  },
  {
    title: "Operational benchmarking",
    description: "Compare baselines, fusion models, runtime, and evaluation metrics.",
    icon: BarChart3
  }
];

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-background">
      <header className="border-b">
        <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-4 lg:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-md border">
              <Cloud className="h-4 w-4" aria-hidden="true" />
            </div>
            <span className="text-sm font-semibold">clearSKY AI</span>
          </div>
          <div className="flex items-center gap-2">
            <Button asChild size="sm" variant="ghost">
              <Link href="/login">Log in</Link>
            </Button>
            <Button asChild size="sm">
              <Link href="/dashboard">
                Open console
                <ArrowRight className="ml-2 h-4 w-4" aria-hidden="true" />
              </Link>
            </Button>
          </div>
        </div>
      </header>

      <section className="mx-auto grid w-full max-w-7xl gap-10 px-4 py-16 lg:grid-cols-[1.05fr_0.95fr] lg:px-6 lg:py-24">
        <div className="flex flex-col justify-center">
          <Badge className="w-fit" variant="secondary">
            LISS-IV cloud removal platform
          </Badge>
          <h1 className="mt-5 max-w-3xl text-balance text-4xl font-semibold tracking-normal md:text-5xl">
            Operational cloud detection and reconstruction for satellite imagery.
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-muted-foreground">
            A minimal research dashboard for uploading cloudy scenes, inspecting masks,
            reviewing reconstruction quality, comparing models, and exporting outputs.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Button asChild>
              <Link href="/dashboard">Enter dashboard</Link>
            </Button>
            <DemoRunButton redirectToDashboard variant="secondary" />
            <Button asChild variant="outline">
              <Link href="/methodology">View methodology</Link>
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Pipeline status</CardTitle>
            <CardDescription>Public CPU-safe workflow with training-ready AI research modules.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {[
              ["Backend API", "Connected"],
              ["Upload validation", "Available"],
              ["Baseline inference", "Operational"],
              ["Advanced weights", "Optional"],
              ["Benchmark reports", "Available"]
            ].map(([label, value]) => (
              <div className="flex items-center justify-between gap-4 text-sm" key={label}>
                <span className="text-muted-foreground">{label}</span>
                <Badge variant={value.includes("Optional") ? "outline" : "secondary"}>{value}</Badge>
              </div>
            ))}
            <Separator />
            <p className="text-sm text-muted-foreground">
              The frontend is intentionally restrained: dense, inspectable, and built for repeated
              research operations.
            </p>
          </CardContent>
        </Card>
      </section>

      <section className="mx-auto w-full max-w-7xl px-4 pb-8 lg:px-6">
        <DemoModeCard redirectToDashboard compact showButton={false} />
      </section>

      <section className="mx-auto grid w-full max-w-7xl gap-4 px-4 pb-16 md:grid-cols-3 lg:px-6">
        {capabilities.map((item) => {
          const Icon = item.icon;
          return (
            <Card key={item.title}>
              <CardHeader>
                <Icon className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
                <CardTitle>{item.title}</CardTitle>
                <CardDescription>{item.description}</CardDescription>
              </CardHeader>
            </Card>
          );
        })}
      </section>
    </main>
  );
}
