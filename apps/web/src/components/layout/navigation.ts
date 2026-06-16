import {
  BarChart3,
  BookOpen,
  Cloud,
  Cpu,
  Database,
  FileText,
  Gauge,
  History,
  LayoutDashboard,
  Settings,
  ShieldCheck,
  Upload,
  UserCircle,
  WandSparkles,
  Workflow
} from "lucide-react";

export const navigationItems = [
  {
    title: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    description: "Operational overview"
  },
  {
    title: "Upload",
    href: "/upload",
    icon: Upload,
    description: "Register LISS-IV scenes"
  },
  {
    title: "Dataset Explorer",
    href: "/datasets",
    icon: Database,
    description: "Inspect scenes and assets"
  },
  {
    title: "Cloud Detection",
    href: "/cloud-detection",
    icon: Cloud,
    description: "Masks and shadow QA"
  },
  {
    title: "Reconstruction",
    href: "/reconstruction",
    icon: WandSparkles,
    description: "Cloud-free outputs"
  },
  {
    title: "Evaluation",
    href: "/evaluation",
    icon: Gauge,
    description: "Spectral and quality metrics"
  },
  {
    title: "Operational Workflow",
    href: "/operational-workflow",
    icon: Workflow,
    description: "Explainability and decisions"
  },
  {
    title: "Benchmarking",
    href: "/benchmarking",
    icon: BarChart3,
    description: "Model comparison"
  },
  {
    title: "Model Registry",
    href: "/model-registry",
    icon: Cpu,
    description: "Versions and checkpoints"
  },
  {
    title: "Training History",
    href: "/training-history",
    icon: History,
    description: "Experiments and metrics"
  },
  {
    title: "Research Dashboard",
    href: "/research-dashboard",
    icon: FileText,
    description: "Reports and exports"
  },
  {
    title: "Methodology",
    href: "/methodology",
    icon: BookOpen,
    description: "Research workflow"
  },
  {
    title: "Settings",
    href: "/settings",
    icon: Settings,
    description: "Runtime preferences"
  },
  {
    title: "Account",
    href: "/account",
    icon: UserCircle,
    description: "User projects"
  }
] as const;

export const qualityItems = [
  {
    label: "Scientific output",
    value: "Guarded",
    icon: ShieldCheck
  },
  {
    label: "Production API",
    value: "Online",
    icon: Gauge
  }
] as const;
