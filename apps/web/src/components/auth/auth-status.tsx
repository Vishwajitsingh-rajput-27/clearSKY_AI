"use client";

import Link from "next/link";
import { useEffect } from "react";
import { LogOut, UserCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useAuthStore } from "@/store/auth-store";

export function AuthStatus() {
  const user = useAuthStore((state) => state.user);
  const token = useAuthStore((state) => state.token);
  const fetchMe = useAuthStore((state) => state.fetchMe);
  const logout = useAuthStore((state) => state.logout);

  useEffect(() => {
    if (token && !user) {
      void fetchMe();
    }
  }, [fetchMe, token, user]);

  if (!token || !user) {
    return (
      <div className="hidden items-center gap-2 sm:flex">
        <Button asChild size="sm" variant="ghost">
          <Link href="/login">Log in</Link>
        </Button>
        <Button asChild size="sm">
          <Link href="/signup">Sign up</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Badge className="hidden max-w-48 truncate sm:inline-flex" variant="secondary">
        <UserCircle className="mr-1.5 h-3.5 w-3.5" />
        {user.full_name || user.email}
      </Badge>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button aria-label="Log out" size="icon" variant="ghost" onClick={logout}>
            <LogOut className="h-4 w-4" />
          </Button>
        </TooltipTrigger>
        <TooltipContent>Log out</TooltipContent>
      </Tooltip>
    </div>
  );
}
