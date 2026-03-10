"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Shield, Loader2 } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const res = await signIn("credentials", {
        email,
        password,
        redirect: false,
      });

      if (res?.error) {
        setError("Invalid email or password");
      } else {
        router.push("/dashboard");
        router.refresh(); // Refresh session
      }
    } catch (err) {
      setError("An unexpected error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[var(--bg-secondary)] px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 rounded-xl bg-[var(--bg-primary)] p-8 shadow-lg sm:p-10 border border-[var(--border-color)]">
        <div>
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-[var(--primary-500)]/10">
            <Shield className="h-10 w-10 text-[var(--primary-500)]" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-[var(--text-primary)]">
            Sign in to DRISK
          </h2>
          <p className="mt-2 text-center text-sm text-[var(--text-secondary)]">
            Digital Risk Intelligence for Security
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-[var(--error)]/10 p-4 text-sm text-[var(--error)] border border-[var(--error)]/20">
              {error}
            </div>
          )}
          
          <div className="space-y-4 rounded-md shadow-sm">
            <div>
              <label htmlFor="email-address" className="block text-sm font-medium text-[var(--text-primary)]">
                Email address
              </label>
              <input
                id="email-address"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="mt-1 relative block w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:border-[var(--primary-500)] focus:outline-none focus:ring-[var(--primary-500)] sm:text-sm"
                placeholder="name@drisk.app"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-[var(--text-primary)]">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="mt-1 relative block w-full rounded-md border border-[var(--border-color)] bg-[var(--bg-primary)] px-3 py-2 text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:border-[var(--primary-500)] focus:outline-none focus:ring-[var(--primary-500)] sm:text-sm"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="remember-me"
                name="remember-me"
                type="checkbox"
                className="h-4 w-4 rounded border-[var(--border-color)] text-[var(--primary-600)] focus:ring-[var(--primary-500)]"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-[var(--text-secondary)]">
                Remember me
              </label>
            </div>

            <div className="text-sm">
              <a href="#" className="font-medium text-[var(--primary-600)] hover:text-[var(--primary-500)]">
                Forgot your password?
              </a>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative flex w-full justify-center rounded-md border border-transparent bg-[var(--primary-600)] py-2 px-4 text-sm font-medium text-white hover:bg-[var(--primary-700)] focus:outline-none focus:ring-2 focus:ring-[var(--primary-500)] focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                "Sign in"
              )}
            </button>
          </div>
          
          <div className="mt-6 border-t border-[var(--border-color)] pt-6 text-center text-xs text-[var(--text-secondary)]">
            <p>Demo Accounts (password: password123)</p>
            <div className="mt-2 grid grid-cols-2 gap-2 text-left">
              <div>admin@drisk.app</div>
              <div>assessor@drisk.app</div>
              <div>manager@drisk.app</div>
              <div>client@drisk.app</div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
