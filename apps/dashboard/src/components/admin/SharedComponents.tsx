"use client";

import React, { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { cn } from "@/lib/utils";

export function SettingField({ label, value, onChange, isSecret = false }: { readonly label: string, readonly value: string, readonly onChange: (v: string) => void, readonly isSecret?: boolean }) {
  const [show, setShow] = useState(!isSecret);
  return (
    <div className="space-y-2">
      <label className="text-[10px] font-bold text-zinc-500 uppercase tracking-[0.2em]">{label}</label>
      <div className="relative">
        <input
          type={show ? "text" : "password"}
          value={value || ""}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-[#0F0F11]/60 border border-white/5 rounded-2xl px-6 py-4 text-white font-mono text-xs focus:border-red-500/30 transition-all outline-none"
        />
        {isSecret && (
          <button onClick={() => setShow(!show)} className="absolute right-6 top-1/2 -translate-y-1/2 text-zinc-600 hover:text-white transition-colors">
            {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        )}
      </div>
    </div>
  );
}

export function StatusCard({ icon: Icon, label, value, color }: { readonly icon: any, readonly label: string, readonly value: string, readonly color: string }) {
  return (
    <div className="p-6 rounded-2xl bg-white/2 border border-white/5 space-y-3">
      <Icon className={cn("h-5 w-5", color)} />
      <div className="space-y-1">
        <span className="text-[9px] font-bold text-zinc-600 uppercase tracking-widest">{label}</span>
        <p className="text-xl font-bold text-white tracking-tight">{value}</p>
      </div>
    </div>
  );
}

export function ThreatCounter({ label, count, color }: { readonly label: string, readonly count: number, readonly color: string }) {
  return (
    <div className="p-4 rounded-2xl bg-white/2 border border-white/5 text-center space-y-2">
      <div className={cn("h-2 w-full rounded-full", color)} style={{ opacity: count > 0 ? 1 : 0.15 }} />
      <p className="text-xl font-bold text-white">{count}</p>
      <p className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest">{label}</p>
    </div>
  );
}
