"use client";

import Link from "next/link";
import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { FolderPlus, History, Lock, UploadCloud } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { MetricCard } from "@/components/shared/metric-card";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from "@/components/ui/table";
import { apiClient } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";

const projectSchema = z.object({
  name: z.string().min(2).max(160),
  description: z.string().max(2000).optional()
});

type ProjectValues = z.infer<typeof projectSchema>;

function formatBytes(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unitIndex = 0;

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }

  return `${value.toFixed(value >= 10 ? 0 : 1)} ${units[unitIndex]}`;
}

function formatDate(value?: string | null) {
  if (!value) {
    return "n/a";
  }

  return new Intl.DateTimeFormat("en", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  }).format(new Date(value));
}

export function AccountPanel() {
  const queryClient = useQueryClient();
  const token = useAuthStore((state) => state.token);
  const user = useAuthStore((state) => state.user);
  const fetchMe = useAuthStore((state) => state.fetchMe);
  const form = useForm<ProjectValues>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      name: "",
      description: ""
    }
  });

  useEffect(() => {
    if (token && !user) {
      void fetchMe();
    }
  }, [fetchMe, token, user]);

  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: apiClient.projects,
    enabled: Boolean(token)
  });
  const historyQuery = useQuery({
    queryKey: ["user-history"],
    queryFn: apiClient.userHistory,
    enabled: Boolean(token)
  });
  const createProject = useMutation({
    mutationFn: apiClient.createProject,
    onSuccess: () => {
      form.reset();
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    }
  });

  if (!token) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lock className="h-4 w-4 text-muted-foreground" />
            Account required
          </CardTitle>
          <CardDescription>Sign in to track projects, storage usage, and processing history.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Button asChild>
            <Link href="/signup">Create account</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/login">Log in</Link>
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (projectsQuery.isLoading || historyQuery.isLoading || !user) {
    return (
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton className="h-32 w-full" key={index} />
        ))}
      </div>
    );
  }

  if (projectsQuery.isError || historyQuery.isError) {
    const error = projectsQuery.error ?? historyQuery.error;
    return (
      <Alert variant="destructive">
        <AlertTitle>Account data unavailable</AlertTitle>
        <AlertDescription>
          {error instanceof Error ? error.message : "Could not load account data."}
        </AlertDescription>
      </Alert>
    );
  }

  const projects = projectsQuery.data ?? [];
  const history = historyQuery.data;
  const storage = history?.storage;
  const onCreateProject = form.handleSubmit((values) => createProject.mutate(values));

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Projects" value={`${projects.length}`} description="User workspaces" icon={FolderPlus} />
        <MetricCard
          title="History"
          value={`${history?.items.length ?? 0}`}
          description="Scenes and inference runs"
          icon={History}
        />
        <MetricCard
          title="Used storage"
          value={formatBytes(storage?.used_storage_bytes ?? user.used_storage_bytes)}
          description="Against user quota"
          icon={UploadCloud}
        />
        <MetricCard
          title="Remaining"
          value={formatBytes(storage?.remaining_storage_bytes ?? 0)}
          description={formatBytes(storage?.storage_quota_bytes ?? user.storage_quota_bytes)}
          icon={Lock}
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Storage limit</CardTitle>
          <CardDescription>Uploads, generated products, reports, and exports count against this quota.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex items-center justify-between gap-3 text-sm">
            <span>{formatBytes(storage?.used_storage_bytes ?? user.used_storage_bytes)} used</span>
            <span className="text-muted-foreground">{storage?.usage_percent.toFixed(1) ?? "0.0"}%</span>
          </div>
          <Progress value={storage?.usage_percent ?? 0} />
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-[22rem_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Create project</CardTitle>
            <CardDescription>Projects group scenes, inference runs, and exports.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={onCreateProject}>
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="project-name">
                  Name
                </label>
                <Input id="project-name" {...form.register("name")} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium" htmlFor="project-description">
                  Description
                </label>
                <Input id="project-description" {...form.register("description")} />
              </div>
              {createProject.isError ? (
                <Alert variant="destructive">
                  <AlertTitle>Project not created</AlertTitle>
                  <AlertDescription>
                    {createProject.error instanceof Error
                      ? createProject.error.message
                      : "Could not create project."}
                  </AlertDescription>
                </Alert>
              ) : null}
              <Button disabled={createProject.isPending} type="submit">
                <FolderPlus className="mr-2 h-4 w-4" />
                {createProject.isPending ? "Creating" : "Create project"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>User projects</CardTitle>
            <CardDescription>Storage usage and lifecycle status for your project workspaces.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Storage</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {projects.map((project) => (
                  <TableRow key={project.id}>
                    <TableCell>
                      <div className="font-medium">{project.name}</div>
                      <div className="text-xs text-muted-foreground">{project.description ?? "No description"}</div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{project.status}</Badge>
                    </TableCell>
                    <TableCell>{formatBytes(project.storage_used_bytes)}</TableCell>
                    <TableCell>{formatDate(project.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>User history</CardTitle>
          <CardDescription>Authenticated scene uploads and inference activity.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Item</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Model</TableHead>
                <TableHead>Quality</TableHead>
                <TableHead>Storage</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(history?.items ?? []).map((item) => (
                <TableRow key={`${item.kind}-${item.id}`}>
                  <TableCell className="font-medium">{item.title}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">{item.kind}</Badge>
                  </TableCell>
                  <TableCell>{item.status}</TableCell>
                  <TableCell>{item.model ?? "n/a"}</TableCell>
                  <TableCell>{item.quality_score?.toFixed(1) ?? "n/a"}</TableCell>
                  <TableCell>{formatBytes(item.storage_bytes)}</TableCell>
                  <TableCell>{formatDate(item.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
