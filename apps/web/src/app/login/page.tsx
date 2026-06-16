import Link from "next/link";
import { Cloud } from "lucide-react";
import { AuthForm } from "@/components/auth/auth-form";

export default function LoginPage() {
  return (
    <main className="flex min-h-screen flex-col bg-background">
      <header className="border-b">
        <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between px-4 lg:px-6">
          <Link className="flex items-center gap-3" href="/">
            <div className="flex h-9 w-9 items-center justify-center rounded-md border">
              <Cloud className="h-4 w-4" aria-hidden="true" />
            </div>
            <span className="text-sm font-semibold">clearSKY AI</span>
          </Link>
        </div>
      </header>
      <section className="flex flex-1 items-center justify-center px-4 py-12">
        <AuthForm mode="login" />
      </section>
    </main>
  );
}
