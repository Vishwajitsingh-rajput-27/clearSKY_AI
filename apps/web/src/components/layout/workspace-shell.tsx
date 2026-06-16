"use client";

import * as React from "react";
import { SidebarContent } from "@/components/layout/sidebar";
import { TopHeader } from "@/components/layout/top-header";

export function WorkspaceShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r bg-background lg:block">
        <SidebarContent />
      </aside>
      <div className="lg:pl-64">
        <TopHeader />
        <main className="mx-auto w-full max-w-7xl px-4 py-6 lg:px-6">{children}</main>
      </div>
    </div>
  );
}

