"use client";

import { Menu, Search } from "lucide-react";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ThemeToggle } from "@/components/theme-toggle";
import { AuthStatus } from "@/components/auth/auth-status";
import { SidebarContent } from "@/components/layout/sidebar";
import { navigationItems } from "@/components/layout/navigation";
import { useUIStore } from "@/store/ui-store";

export function TopHeader() {
  const pathname = usePathname();
  const sidebarOpen = useUIStore((state) => state.sidebarOpen);
  const setSidebarOpen = useUIStore((state) => state.setSidebarOpen);
  const current = navigationItems.find((item) => item.href === pathname);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80 lg:px-6">
      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              aria-label="Open navigation"
              className="lg:hidden"
              size="icon"
              variant="ghost"
              onClick={() => setSidebarOpen(true)}
            >
              <Menu className="h-4 w-4" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Open navigation</TooltipContent>
        </Tooltip>
        <SheetContent className="w-72 p-0" side="left">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <SidebarContent />
        </SheetContent>
      </Sheet>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{current?.title ?? "Workspace"}</p>
        <p className="hidden truncate text-xs text-muted-foreground sm:block">
          {current?.description ?? "Operational console"}
        </p>
      </div>

      <div className="hidden w-full max-w-sm items-center gap-2 rounded-md border bg-background px-3 md:flex">
        <Search className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
        <Input
          aria-label="Search workspace"
          className="h-9 border-0 px-0 shadow-none focus-visible:ring-0 focus-visible:ring-offset-0"
          placeholder="Search scenes, jobs, metrics"
        />
      </div>

      <AuthStatus />
      <ThemeToggle />
    </header>
  );
}
