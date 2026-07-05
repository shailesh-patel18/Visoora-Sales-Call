"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import DemoReport from "../../components/DemoReport";
import { PublicNavbar } from "../../components/public-navbar";
import { PublicFooter } from "../../components/public-footer";

export default function ReportPage() {
  const { id } = useParams();
  const router = useRouter();
  
  const [analysisData, setAnalysisData] = useState<any>(null);
  const [demoError, setDemoError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;

    const fetchReport = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/public/report/${id}`);
        if (!res.ok) {
          throw new Error("Failed to load report or report expired.");
        }
        const data = await res.json();
        setAnalysisData(data);
      } catch (err: any) {
        setDemoError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
  }, [id]);

  return (
    <main className="min-h-screen bg-[hsl(var(--background))] text-[hsl(var(--foreground))] selection:bg-[hsl(var(--brand-primary))] selection:text-white">
      <PublicNavbar />
      
      <div className="pt-24 pb-20">
        <div className="max-w-6xl mx-auto px-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-32">
              <div className="w-12 h-12 border-4 border-[hsl(var(--brand-primary))] border-t-transparent rounded-full animate-spin"></div>
              <p className="mt-6 text-[hsl(var(--text-muted))]">Loading your Business Brain...</p>
            </div>
          ) : (
            <DemoReport analysisData={analysisData} demoPhase={11} demoError={demoError} />
          )}
        </div>
      </div>

      <PublicFooter />
    </main>
  );
}
