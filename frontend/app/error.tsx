"use client";

import { useEffect } from "react";
import { AlertTriangle, RefreshCcw } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service in production
    console.error("Global Error Boundary caught:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-black flex flex-col items-center justify-center p-4">
      <div className="bg-[#111] border border-red-500/30 rounded-2xl p-8 max-w-md w-full shadow-[0_0_50px_rgba(239,68,68,0.15)] text-center relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-1 bg-red-500"></div>
        
        <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
          <AlertTriangle className="w-8 h-8 text-red-500" />
        </div>
        
        <h2 className="text-2xl font-bold text-white mb-2">System Disconnected</h2>
        <p className="text-gray-400 mb-8 text-sm">
          Visoora encountered an unexpected error connecting to the AI operating system. 
          {process.env.NODE_ENV === "development" && (
            <span className="block mt-4 text-xs text-red-400 text-left bg-black/50 p-2 rounded overflow-auto max-h-32">
              {error.message}
            </span>
          )}
        </p>
        
        <button
          onClick={() => reset()}
          className="w-full flex items-center justify-center gap-2 bg-white text-black font-bold py-3 px-6 rounded-xl hover:bg-gray-200 transition-colors"
        >
          <RefreshCcw className="w-4 h-4" />
          Attempt Recovery
        </button>
      </div>
    </div>
  );
}
