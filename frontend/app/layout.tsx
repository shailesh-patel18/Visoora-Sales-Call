import "./globals.css";
import type { Metadata } from "next";
import { Providers } from "./providers";
import { Sidebar } from "./components/sidebar";

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
      <body className="min-h-screen antialiased">
        <Providers>
          <div className="flex h-screen overflow-hidden">
            <Sidebar />
            <main className="flex-1 overflow-y-auto">{children}</main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
