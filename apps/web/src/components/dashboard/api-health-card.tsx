"use client";

import { useQuery } from "@tanstack/react-query";
import { Server } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiBaseUrl, apiClient } from "@/lib/api";

export function ApiHealthCard() {
  const health = useQuery({
    queryKey: ["api-health"],
    queryFn: apiClient.health
  });

  if (health.isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-4 w-32" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-8 w-40" />
          <Skeleton className="mt-3 h-3 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (health.isError) {
    return (
      <Alert variant="destructive">
        <AlertTitle>API unavailable</AlertTitle>
        <AlertDescription>Could not reach {apiBaseUrl}. Check the backend service.</AlertDescription>
      </Alert>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">API health</CardTitle>
        <Server className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-2xl font-semibold">{health.data?.status ?? "unknown"}</p>
            <p className="mt-1 text-xs text-muted-foreground">{apiBaseUrl}</p>
          </div>
          <Badge variant="secondary">{health.data?.environment ?? "local"}</Badge>
        </div>
      </CardContent>
    </Card>
  );
}

