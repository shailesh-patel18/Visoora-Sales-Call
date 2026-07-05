import "./globals.css";
import type { Metadata } from "next";
import { Providers } from "./providers";
import { LayoutWrapper } from "./components/layout-wrapper";

export const metadata: Metadata = {
  title: "Visoora — AI Sales Command Center",
  description:
    "Manage CRM contacts, track deal pipelines, listen to AI sales call recordings, and monitor live outbound/inbound calls.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning className="min-h-screen antialiased bg-[hsl(var(--surface-0))]">
        <Providers>
          <LayoutWrapper>{children}</LayoutWrapper>
        </Providers>
      </body>
    </html>
  );
}

