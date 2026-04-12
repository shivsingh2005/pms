import type { Metadata } from "next";
import { DM_Sans, Syne } from "next/font/google";
import "./globals.css";
import { AppProviders } from "@/components/providers/app-providers";
import { AppShell } from "@/components/providers/app-shell";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
  weight: ["400", "500", "600", "700"],
  display: "swap",
  preload: true,
});

const syne = Syne({
  subsets: ["latin"],
  variable: "--font-syne",
  weight: ["600", "700"],
  display: "swap",
  preload: true,
});

export const metadata: Metadata = {
  title: "PMS - Performance Management",
  description: "AI-native performance management system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className={`${dmSans.variable} ${syne.variable}`}>
      <body
        className="min-h-screen bg-background font-sans text-foreground antialiased"
      >
        <AppProviders>
          <AppShell>{children}</AppShell>
        </AppProviders>
      </body>
    </html>
  );
}
