"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Loader2, BookOpen } from "lucide-react";
import { fetchPostMortem } from "@/lib/api";
import { PostMortemData } from "@/lib/types";
import { PostMortemViewer } from "@/components/PostMortemViewer";

export default function PostMortemDetailPage() {
  const params = useParams();
  const threadId = (params?.id as string) || "INC-PROD-001";

  const [postMortem, setPostMortem] = useState<PostMortemData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadReport = async () => {
      try {
        const data = await fetchPostMortem(threadId);
        setPostMortem(data);
      } finally {
        setIsLoading(false);
      }
    };

    loadReport();
  }, [threadId]);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Back Button */}
      <div className="flex items-center gap-2">
        <Link
          href="/post-mortems"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Knowledge Base</span>
        </Link>
        <span className="text-slate-600">/</span>
        <span className="text-xs font-mono text-indigo-400 font-semibold">
          {threadId}
        </span>
      </div>

      {isLoading ? (
        <div className="py-24 text-center">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-500 mx-auto mb-3" />
          <p className="text-xs text-slate-400">
            Loading Google SRE Post-Mortem Report...
          </p>
        </div>
      ) : postMortem ? (
        <PostMortemViewer data={postMortem} />
      ) : (
        <div className="rounded-2xl bg-surface-900 border border-hairline p-12 text-center">
          <BookOpen className="h-10 w-10 text-slate-600 mx-auto mb-3" />
          <h3 className="text-white font-semibold text-base mb-1">
            Post-Mortem Not Available Yet
          </h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mb-4">
            The incident may still be actively investigating or waiting for human approval.
          </p>
          <Link
            href={`/incidents/${threadId}`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-colors"
          >
            Go to War Room Command Center
          </Link>
        </div>
      )}
    </div>
  );
}
