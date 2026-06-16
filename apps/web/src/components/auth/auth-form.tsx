"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { zodResolver } from "@hookform/resolvers/zod";
import { LogIn, UserPlus } from "lucide-react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/store/auth-store";

const baseSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8, "Use at least 8 characters.")
});

const signupSchema = baseSchema.extend({
  full_name: z.string().max(160).optional()
});

type AuthMode = "login" | "signup";
type LoginValues = z.infer<typeof baseSchema>;
type SignupValues = z.infer<typeof signupSchema>;

export function AuthForm({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  const signup = useAuthStore((state) => state.signup);
  const status = useAuthStore((state) => state.status);
  const errorMessage = useAuthStore((state) => state.errorMessage);
  const schema = mode === "signup" ? signupSchema : baseSchema;
  const form = useForm<SignupValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: "",
      password: "",
      full_name: ""
    }
  });
  const isSignup = mode === "signup";

  const onSubmit = form.handleSubmit(async (values) => {
    if (isSignup) {
      await signup(values);
    } else {
      await login(values as LoginValues);
    }

    router.push("/dashboard");
  });

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>{isSignup ? "Create account" : "Log in"}</CardTitle>
        <CardDescription>
          {isSignup
            ? "Create a clearSKY AI account for projects, history, and storage limits."
            : "Access your clearSKY AI projects and processing history."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={onSubmit}>
          {isSignup ? (
            <div className="space-y-2">
              <label className="text-sm font-medium" htmlFor="full_name">
                Name
              </label>
              <Input id="full_name" autoComplete="name" {...form.register("full_name")} />
            </div>
          ) : null}

          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="email">
              Email
            </label>
            <Input id="email" autoComplete="email" type="email" {...form.register("email")} />
            {form.formState.errors.email ? (
              <p className="text-sm text-destructive">{form.formState.errors.email.message}</p>
            ) : null}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="password">
              Password
            </label>
            <Input
              id="password"
              autoComplete={isSignup ? "new-password" : "current-password"}
              type="password"
              {...form.register("password")}
            />
            {form.formState.errors.password ? (
              <p className="text-sm text-destructive">{form.formState.errors.password.message}</p>
            ) : null}
          </div>

          {errorMessage ? (
            <Alert variant="destructive">
              <AlertTitle>{isSignup ? "Signup failed" : "Login failed"}</AlertTitle>
              <AlertDescription>{errorMessage}</AlertDescription>
            </Alert>
          ) : null}

          <Button className="w-full" disabled={status === "loading"} type="submit">
            {isSignup ? <UserPlus className="mr-2 h-4 w-4" /> : <LogIn className="mr-2 h-4 w-4" />}
            {status === "loading" ? "Please wait" : isSignup ? "Create account" : "Log in"}
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-muted-foreground">
          {isSignup ? "Already have an account?" : "New to clearSKY AI?"}{" "}
          <Link className="font-medium text-foreground underline-offset-4 hover:underline" href={isSignup ? "/login" : "/signup"}>
            {isSignup ? "Log in" : "Create account"}
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
