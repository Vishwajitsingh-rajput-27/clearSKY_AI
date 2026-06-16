import { Inbox } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

type EmptyStateProps = {
  title: string;
  description: string;
  action?: string;
};

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <Card>
      <CardContent className="flex min-h-52 flex-col items-center justify-center p-8 text-center">
        <Inbox className="mb-3 h-8 w-8 text-muted-foreground" aria-hidden="true" />
        <h3 className="text-sm font-medium">{title}</h3>
        <p className="mt-2 max-w-sm text-sm text-muted-foreground">{description}</p>
        {action ? (
          <Button className="mt-4" variant="outline">
            {action}
          </Button>
        ) : null}
      </CardContent>
    </Card>
  );
}

