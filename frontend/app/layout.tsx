import "./globals.css";
import type { Metadata } from "next";
import { Inter, Outfit } from "next/font/google";
import { Providers } from "./providers";
import { LayoutWrapper } from "./components/layout-wrapper";
import { Toaster } from "sonner";
import { DevToolsWidget } from "./components/DevToolsWidget";

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });
const outfit = Outfit({ subsets: ['latin'], variable: '--font-outfit' });

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
      <body suppressHydrationWarning className={`${inter.variable} ${outfit.variable} font-sans min-h-screen antialiased bg-[hsl(var(--surface-0))]`}>
        <Providers>
          <LayoutWrapper>{children}</LayoutWrapper>
          <DevToolsWidget />
          <Toaster richColors position="top-right" theme="dark" />
        </Providers>
      </body>
    </html>
  );
}
