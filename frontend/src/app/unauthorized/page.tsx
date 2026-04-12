"use client";

import Link from "next/link";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function UnauthorizedPage() {
  return (
    <div className="mx-auto flex min-h-[70vh] max-w-2xl items-center px-6">
      <Card className="w-full space-y-4 rounded-2xl border border-border/75 bg-card/95 p-8 text-center">
        <CardTitle>Access Restricted</CardTitle>
        <CardDescription>
          Your account does not have access to this page. Use the dashboard that matches your role.
        </CardDescription>
        <div className="flex flex-wrap justify-center gap-3">
          <Link href="/">
            <Button>Go Home</Button>
          </Link>
          <Link href="/login">
            <Button variant="outline">Sign In Again</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
