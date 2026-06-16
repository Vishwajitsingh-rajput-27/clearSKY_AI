"use client";

import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { apiClient } from "@/lib/api";
import { scenes } from "@/lib/mock-data";
import { useUIStore } from "@/store/ui-store";

export function SceneTable() {
  const setSelectedSceneId = useUIStore((state) => state.setSelectedSceneId);
  const liveScenes = useQuery({
    queryKey: ["scenes"],
    queryFn: apiClient.scenes
  });

  const rows = liveScenes.data?.length
    ? liveScenes.data.map((scene) => ({
        id: scene.id,
        name: scene.original_filename ?? scene.filename,
        region: "Uploaded",
        sensor: scene.sensor,
        cloud: 0,
        shadow: 0,
        status: scene.status,
        date: scene.created_at?.slice(0, 10) ?? "Local"
      }))
    : scenes;

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Scene</TableHead>
          <TableHead>Region</TableHead>
          <TableHead>Sensor</TableHead>
          <TableHead>Cloud</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Date</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((scene) => (
          <TableRow
            className="cursor-pointer"
            key={scene.id}
            onClick={() => setSelectedSceneId(scene.id)}
          >
            <TableCell className="font-medium">{scene.name}</TableCell>
            <TableCell>{scene.region}</TableCell>
            <TableCell>{scene.sensor}</TableCell>
            <TableCell>{scene.cloud}%</TableCell>
            <TableCell>
              <Badge variant={scene.status === "Ready" || scene.status === "uploaded" ? "secondary" : "outline"}>
                {scene.status}
              </Badge>
            </TableCell>
            <TableCell className="text-muted-foreground">{scene.date}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

