import { Badge } from "@/components/ui/badge";

type PageHeaderProps = {
  title: string;
  description: string;
  eyebrow?: string;
};

export function PageHeader({ title, description, eyebrow }: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-2">
      {eyebrow ? (
        <Badge className="w-fit" variant="secondary">
          {eyebrow}
        </Badge>
      ) : null}
      <div>
        <h1 className="text-2xl font-semibold tracking-normal">{title}</h1>
        <p className="mt-1 max-w-3xl text-sm text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}

