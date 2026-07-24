import "./globals.css";

import type { Metadata } from "next";

import { AppNav } from "@/components/app-nav";

export const metadata: Metadata = {
  title: "AgentGuard",
  description: "Release gate dashboard for AI agent reliability testing",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AppNav />
        <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
