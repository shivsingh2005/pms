"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { authService } from "@/services/auth";
import { useSessionStore } from "@/store/useSessionStore";
import { Button } from "@/components/ui/button";

function GoogleCallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const setGoogleAccessToken = useSessionStore((state) => state.setGoogleAccessToken);
  const [status, setStatus] = useState("Completing Google sign-in...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = searchParams.get("code");
    const authError = searchParams.get("error");

    if (authError) {
      setError(`Google authorization failed: ${authError}`);
      setStatus("Authorization failed");
      return;
    }

    if (!code) {
      setError("Missing authorization code from Google callback");
      setStatus("Authorization failed");
      return;
    }

    authService
      .exchangeGoogleCode({ code, redirect_uri: window.location.origin + "/auth/google/callback" })
      .then((token) => {
        if (!token.access_token) {
          throw new Error("Google token exchange returned empty access token");
        }
        setGoogleAccessToken(token.access_token);
        setStatus("Google Calendar connected. Redirecting to Meetings...");
        setTimeout(() => router.push("/meetings"), 700);
      })
      .catch((exchangeError: unknown) => {
        const message =
          exchangeError && typeof exchangeError === "object" && "message" in exchangeError
            ? String((exchangeError as { message: string }).message)
            : "Google token exchange failed";
        setError(message);
        setStatus("Authorization failed");
      });
  }, [router, searchParams, setGoogleAccessToken]);

  return (
    <div className="grid min-h-[72vh] place-items-center">
      <Card className="w-full max-w-xl space-y-3">
        <CardTitle>Google Calendar Setup</CardTitle>
        <CardDescription>{status}</CardDescription>
        {error ? <p className="text-sm text-error">{error}</p> : null}
        <div className="pt-2">
          <Button variant="outline" onClick={() => router.push("/meetings")}>Back to Meetings</Button>
        </div>
      </Card>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="grid min-h-[72vh] place-items-center">
          <Card className="w-full max-w-xl space-y-3">
            <CardTitle>Google Calendar Setup</CardTitle>
            <CardDescription>Completing Google sign-in...</CardDescription>
          </Card>
        </div>
      }
    >
      <GoogleCallbackContent />
    </Suspense>
  );
}
