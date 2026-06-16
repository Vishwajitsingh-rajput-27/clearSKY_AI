"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Cloud } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { navigationItems, qualityItems } from "@/components/layout/navigation";
import { useUIStore } from "@/store/ui-store";

export function SidebarContent() {
  const pathname = usePathname();
  const productMode = useUIStore((state) => state.productMode);
  const setSidebarOpen = useUIStore((state) => state.setSidebarOpen);

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center gap-3 px-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-md border bg-background">
          <Cloud className="h-4 w-4" aria-hidden="true" />
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold">clearSKY AI</p>
          <p className="truncate text-xs text-muted-foreground">LISS-IV research ops</p>
        </div>
      </div>

      <Separator />

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href;

          return (
            <Link
              href={item.href}
              key={item.href}
              onClick={() => setSidebarOpen(false)}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
              <span className="truncate">{item.title}</span>
            </Link>
          );
        })}
      </nav>

      <div className="space-y-3 border-t p-4">
        <div className="flex items-center justify-between gap-3">
          <span className="text-xs text-muted-foreground">Mode</span>
          <Badge variant="secondary">
            {productMode === "scientific" ? "Scientific" : "Visual"}
          </Badge>
        </div>
        <div className="grid gap-2">
          {qualityItems.map((item) => {
            const Icon = item.icon;
            return (
              <div className="flex items-center justify-between gap-3 text-xs" key={item.label}>
                <span className="flex items-center gap-2 text-muted-foreground">
                  <Icon className="h-3.5 w-3.5" aria-hidden="true" />
                  {item.label}
                </span>
                <span className="font-medium">{item.value}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

