"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Save } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useUIStore } from "@/store/ui-store";

const settingsSchema = z.object({
  productMode: z.enum(["scientific", "visual"]),
  maxUploadMb: z.coerce.number().min(1).max(2048),
  defaultModel: z.enum(["foundation", "attention-unet", "liss-fuseswin"])
});

type SettingsValues = z.infer<typeof settingsSchema>;

export function SettingsForm() {
  const productMode = useUIStore((state) => state.productMode);
  const setProductMode = useUIStore((state) => state.setProductMode);

  const form = useForm<SettingsValues>({
    resolver: zodResolver(settingsSchema),
    defaultValues: {
      productMode,
      maxUploadMb: 512,
      defaultModel: "foundation"
    }
  });

  const onSubmit = form.handleSubmit((values) => {
    setProductMode(values.productMode);
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Workspace preferences</CardTitle>
        <CardDescription>Local UI preferences only. Backend settings still come from environment variables.</CardDescription>
      </CardHeader>
      <CardContent>
        <form className="grid gap-5 md:grid-cols-2" onSubmit={onSubmit}>
          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="productMode">
              Product mode
            </label>
            <Select
              defaultValue={productMode}
              onValueChange={(value) => form.setValue("productMode", value as SettingsValues["productMode"])}
            >
              <SelectTrigger id="productMode">
                <SelectValue placeholder="Select mode" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="scientific">Scientific</SelectItem>
                <SelectItem value="visual">Visual</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="defaultModel">
              Default model
            </label>
            <Select
              defaultValue="foundation"
              onValueChange={(value) => form.setValue("defaultModel", value as SettingsValues["defaultModel"])}
            >
              <SelectTrigger id="defaultModel">
                <SelectValue placeholder="Select model" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="foundation">Foundation fallback</SelectItem>
                <SelectItem value="attention-unet">Attention U-Net</SelectItem>
                <SelectItem value="liss-fuseswin">LISS-FuseSwin</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="maxUploadMb">
              Max upload MB
            </label>
            <Input id="maxUploadMb" type="number" {...form.register("maxUploadMb")} />
            {form.formState.errors.maxUploadMb ? (
              <p className="text-sm text-destructive">{form.formState.errors.maxUploadMb.message}</p>
            ) : null}
          </div>

          <div className="flex items-end">
            <Button type="submit">
              <Save className="mr-2 h-4 w-4" aria-hidden="true" />
              Save preferences
            </Button>
          </div>

          {form.formState.isSubmitSuccessful ? (
            <Alert className="md:col-span-2">
              <AlertTitle>Preferences saved</AlertTitle>
              <AlertDescription>The workspace mode has been updated locally.</AlertDescription>
            </Alert>
          ) : null}
        </form>
      </CardContent>
    </Card>
  );
}
