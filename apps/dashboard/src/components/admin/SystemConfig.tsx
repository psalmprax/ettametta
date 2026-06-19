"use client";

import React from "react";
import {
    Activity,
    Monitor,
    Cpu,
    HardDrive,
    ShieldCheck,
    Webhook,
    DollarSign,
    Repeat,
    RotateCw,
    AlertCircle,
    ArrowUpRight,
    Shield,
    FileText,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { StatusCard, ThreatCounter } from "./SharedComponents";
import { Button } from "@/components/ui/Button";

export function InfrastructureStatus({ systemStatus, setIsClusterManagerOpen }: { readonly systemStatus: any, readonly setIsClusterManagerOpen: (v: boolean) => void }) {
  return (
    <div className="space-y-10">
      <div className="flex items-center justify-between">
        <h3 className="text-2xl font-bold text-white uppercase tracking-widest">Node Infrastructure</h3>
        <button
          onClick={() => setIsClusterManagerOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-[10px] font-bold text-cyan-400 uppercase tracking-wider hover:bg-cyan-500/20 transition-colors"
        >
          <Cpu className="h-3.5 w-3.5" />
          Manage Cluster
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <StatusCard icon={Cpu} label="CPU Load" value={systemStatus?.cpu_load || "0%"} color="text-cyan-400" />
        <StatusCard icon={HardDrive} label="Memory" value={systemStatus?.memory_usage || "0%"} color="text-violet-400" />
        <StatusCard icon={Activity} label="Latency" value={systemStatus?.latency || "0ms"} color="text-emerald-400" />
        <StatusCard icon={Monitor} label="Uptime" value={systemStatus?.uptime || "0h"} color="text-amber-400" />
      </div>
    </div>
  );
}

export function WebhooksTab({ webhookStats }: { readonly webhookStats: any }) {
  return (
    <div className="space-y-10">
      <h3 className="text-2xl font-bold text-white uppercase tracking-widest">Webhook Monitor</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <StatusCard icon={Webhook} label="Total Processed" value={String(webhookStats?.total_processed ?? "—")} color="text-cyan-400" />
        <StatusCard icon={RotateCw} label="Renewals" value={String(webhookStats?.total_renewals ?? "—")} color="text-violet-400" />
        <StatusCard icon={DollarSign} label="Credits Granted" value={String(webhookStats?.total_credits_granted ?? "—")} color="text-emerald-400" />
        <StatusCard icon={Repeat} label="Duplicates Skipped" value={String(webhookStats?.total_skipped ?? "—")} color="text-amber-400" />
      </div>

      <div className="p-6 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold text-white uppercase tracking-widest">Recent Purchase Events</h4>
          <span className="text-[8px] font-mono text-cyan-500/50">STRIPE_WEBHOOK_LEDGER</span>
        </div>
        {webhookStats?.recent?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest border-b border-white/5">
                  <th className="pb-3 pr-4">User</th>
                  <th className="pb-3 pr-4">Amount</th>
                  <th className="pb-3 pr-4">Session ID</th>
                  <th className="pb-3 pr-4">Description</th>
                  <th className="pb-3">Time</th>
                </tr>
              </thead>
              <tbody className="text-[10px]">
                {webhookStats.recent.map((tx: any) => (
                  <tr key={tx.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="py-3 pr-4 font-mono text-zinc-400">{tx.user_id}</td>
                    <td className="py-3 pr-4 font-bold text-emerald-400">+{tx.amount}</td>
                    <td className="py-3 pr-4 font-mono text-zinc-500">{tx.reference_id || "—"}</td>
                    <td className="py-3 pr-4 text-zinc-400 max-w-[200px] truncate">{tx.description || "—"}</td>
                    <td className="py-3 text-zinc-600 whitespace-nowrap">
                      {tx.created_at ? new Date(tx.created_at).toLocaleString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center">
            <Webhook className="h-8 w-8 text-zinc-800 mx-auto mb-2" />
            <p className="text-xs font-bold text-zinc-600 uppercase tracking-wider">No webhook events recorded</p>
            <p className="text-[9px] text-zinc-700 mt-1">Events appear after users purchase credits via Stripe</p>
          </div>
        )}
      </div>

      <div className="p-6 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-4">
        <h4 className="text-xs font-bold text-white uppercase tracking-widest">Idempotency Status</h4>
        <div className="flex items-center gap-4 p-4 rounded-2xl bg-emerald-500/5 border border-emerald-500/10">
          <ShieldCheck className="h-6 w-6 text-emerald-500 shrink-0" />
          <div className="space-y-0.5">
            <p className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Protection Active</p>
            <p className="text-[9px] text-zinc-500">
              Credit purchase webhooks check CreditTransactionDB for existing reference_id before granting credits.
              Duplicate Stripe retries are automatically skipped.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export function SecurityHub({ securityStatus, securityEvents, isAuditing, isScanning, auditResult, scanResult, triggerAudit, triggerVulnerabilityScan }: {
  readonly securityStatus: any,
  readonly securityEvents: any[],
  readonly isAuditing: boolean,
  readonly isScanning: boolean,
  readonly auditResult: any,
  readonly scanResult: any,
  readonly triggerAudit: () => void,
  readonly triggerVulnerabilityScan: () => void,
}) {
  return (
    <div className="space-y-10">
      <h3 className="text-2xl font-bold text-white uppercase tracking-widest">Security Sentinel</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
        <StatusCard icon={Shield} label="Health Score" value={`${securityStatus?.health_score ?? "—"}%`} color={securityStatus?.health_score && securityStatus.health_score >= 80 ? "text-emerald-400" : "text-red-500"} />
        <StatusCard icon={Activity} label="Threat Level" value={securityStatus?.threat_level || "NOMINAL"} color={securityStatus?.threat_level === "CRITICAL" || securityStatus?.threat_level === "HIGH" ? "text-red-500" : securityStatus?.threat_level === "MEDIUM" ? "text-amber-400" : "text-emerald-400"} />
        <StatusCard icon={ShieldCheck} label="System Integrity" value={securityStatus?.system_integrity || "NOMINAL"} color={securityStatus?.system_integrity === "CRITICAL" ? "text-red-500" : securityStatus?.system_integrity === "DEGRADED" ? "text-amber-400" : "text-emerald-400"} />
        <StatusCard icon={FileText} label="Recent Threats" value={String(securityStatus?.recent_threats?.length ?? 0)} color="text-amber-400" />
      </div>

      {securityStatus?.threat_breakdown && (
        <div className="p-6 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-4">
          <h4 className="text-xs font-bold text-white uppercase tracking-widest">Threat Breakdown (Last 100 Events)</h4>
          <div className="grid grid-cols-4 gap-4">
            <ThreatCounter label="Critical" count={securityStatus.threat_breakdown.critical ?? 0} color="bg-red-500" />
            <ThreatCounter label="High" count={securityStatus.threat_breakdown.high ?? 0} color="bg-orange-500" />
            <ThreatCounter label="Medium" count={securityStatus.threat_breakdown.medium ?? 0} color="bg-amber-500" />
            <ThreatCounter label="Low" count={securityStatus.threat_breakdown.low ?? 0} color="bg-zinc-500" />
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-4">
          <div className="flex items-center gap-3">
            <ShieldCheck className="h-6 w-6 text-red-500" />
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-widest">Integrity Audit</h4>
              <p className="text-[9px] text-zinc-500 mt-0.5">Full system integrity check — SECRET_KEY, file permissions, open ports</p>
            </div>
          </div>
          <Button
            onClick={triggerAudit}
            disabled={isAuditing}
            className="w-full bg-red-500 hover:bg-red-400 text-white font-bold h-12 rounded-2xl"
          >
            {isAuditing ? "Auditing..." : "Run Audit"}
          </Button>
          {auditResult && (
            <div className="space-y-2 pt-2">
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/3 border border-white/5">
                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Score</span>
                <span className={cn("text-sm font-bold", (auditResult?.report?.score ?? 0) >= 80 ? "text-emerald-400" : "text-red-500")}>
                  {auditResult?.report?.score ?? "?"}%
                </span>
              </div>
              {auditResult?.report?.findings?.length > 0 && (
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {auditResult.report.findings.map((f: string, i: number) => (
                    <div key={i} className="flex items-start gap-2 p-2 rounded-xl bg-red-500/5 border border-red-500/10">
                      <AlertCircle className="h-3 w-3 text-red-500 shrink-0 mt-0.5" />
                      <span className="text-[9px] text-zinc-400 leading-relaxed">{f}</span>
                    </div>
                  ))}
                </div>
              )}
              {(!auditResult?.report?.findings || auditResult.report.findings.length === 0) && (
                <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
                  <p className="text-[9px] text-emerald-400 font-bold uppercase tracking-wider text-center">No findings — system is clean</p>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="p-6 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-4">
          <div className="flex items-center gap-3">
            <Cpu className="h-6 w-6 text-violet-500" />
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-widest">Vulnerability Scan</h4>
              <p className="text-[9px] text-zinc-500 mt-0.5">Scans for debug mode, hardcoded secrets, and misconfigurations</p>
            </div>
          </div>
          <Button
            onClick={triggerVulnerabilityScan}
            disabled={isScanning}
            className="w-full bg-violet-500 hover:bg-violet-400 text-white font-bold h-12 rounded-2xl"
          >
            {isScanning ? "Scanning..." : "Run Vulnerability Scan"}
          </Button>
          {scanResult?.scan_results && scanResult.scan_results.length > 0 && (
            <div className="space-y-1 max-h-40 overflow-y-auto pt-2">
              {scanResult.scan_results.map((v: any, i: number) => (
                <div key={i} className="flex items-start gap-2 p-2 rounded-xl bg-red-500/5 border border-red-500/10">
                  <AlertCircle className={cn("h-3 w-3 shrink-0 mt-0.5", v.severity === "critical" ? "text-red-500" : v.severity === "high" ? "text-orange-500" : "text-amber-500")} />
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-[8px] font-bold uppercase tracking-wider text-red-500">{v.severity}</span>
                      <span className="text-[9px] text-zinc-300 font-bold">{v.type}</span>
                    </div>
                    <p className="text-[8px] text-zinc-500 leading-relaxed">{v.description}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
          {scanResult && (!scanResult.scan_results || scanResult.scan_results.length === 0) && (
            <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/10">
              <p className="text-[9px] text-emerald-400 font-bold uppercase tracking-wider text-center">No vulnerabilities found — system is clean</p>
            </div>
          )}
        </div>
      </div>

      <div className="p-6 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold text-white uppercase tracking-widest">Recent Security Events</h4>
          <span className="text-[8px] font-mono text-red-500/50">SENTINEL_LOG</span>
        </div>
        {securityEvents.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="text-[8px] font-bold text-zinc-600 uppercase tracking-widest border-b border-white/5">
                  <th className="pb-3 pr-4">Severity</th>
                  <th className="pb-3 pr-4">Type</th>
                  <th className="pb-3 pr-4">Details</th>
                  <th className="pb-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="text-[10px]">
                {securityEvents.map((event: any, i: number) => (
                  <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="py-3 pr-4">
                      <span className={cn(
                        "px-2 py-0.5 rounded-full text-[8px] font-bold uppercase tracking-wider",
                        event.severity === "critical" ? "bg-red-500/20 text-red-500 border border-red-500/30" :
                        event.severity === "high" ? "bg-orange-500/20 text-orange-500 border border-orange-500/30" :
                        event.severity === "medium" ? "bg-amber-500/20 text-amber-500 border border-amber-500/30" :
                        "bg-zinc-500/20 text-zinc-400 border border-zinc-500/30"
                      )}>
                        {event.severity || "low"}
                      </span>
                    </td>
                    <td className="py-3 pr-4 font-mono text-zinc-300">{event.type || "—"}</td>
                    <td className="py-3 pr-4 max-w-[250px] truncate text-zinc-500">
                      {event.details ? (() => {
                        const d = typeof event.details === "string" ? event.details : JSON.stringify(event.details);
                        return d.length > 60 ? d.slice(0, 60) + "..." : d;
                      })() : "—"}
                    </td>
                    <td className="py-3 text-zinc-600 whitespace-nowrap">
                      {event.timestamp ? new Date(event.timestamp).toLocaleString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center">
            <Shield className="h-8 w-8 text-zinc-800 mx-auto mb-2" />
            <p className="text-xs font-bold text-zinc-600 uppercase tracking-wider">No security events recorded</p>
            <p className="text-[9px] text-zinc-700 mt-1">Events appear when sentinel detects anomalies or threats</p>
          </div>
        )}
      </div>
    </div>
  );
}

export function AuditsTab({ securityStatus, securityEvents, isAuditing, triggerAudit }: {
  readonly securityStatus: any,
  readonly securityEvents: any[],
  readonly isAuditing: boolean,
  readonly triggerAudit: () => void,
}) {
  return (
    <div className="space-y-10">
      <h3 className="text-2xl font-bold text-white uppercase tracking-widest">Admin Audits</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <a
          href="/admin/audits"
          className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6 hover:border-cyan-500/30 transition-all group"
        >
          <div className="h-16 w-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center group-hover:scale-110 transition-transform">
            <FileText className="h-8 w-8 text-cyan-400" />
          </div>
          <div className="space-y-2">
            <h4 className="text-lg font-bold text-white uppercase tracking-tight">Governance Engine</h4>
            <p className="text-xs text-zinc-500 leading-relaxed">
              Full compliance & security audit suite — account audits, red-team integrity scans,
              bias neutrality checks, and governance telemetry logs.
            </p>
          </div>
          <div className="flex items-center gap-2 text-cyan-400 text-[10px] font-bold uppercase tracking-widest group-hover:gap-3 transition-all">
            Open Audit Console
            <ArrowUpRight className="h-3 w-3" />
          </div>
        </a>

        <div className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6">
          <div className="h-16 w-16 rounded-2xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
            <ShieldCheck className="h-8 w-8 text-violet-400" />
          </div>
          <div className="space-y-2">
            <h4 className="text-lg font-bold text-white uppercase tracking-tight">Latest Scan Results</h4>
            <div className="space-y-3 mt-4">
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/3 border border-white/5">
                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">System Integrity</span>
                <span className={cn("text-sm font-bold", (securityStatus?.health_score ?? 0) >= 80 ? "text-emerald-400" : "text-red-500")}>
                  {securityStatus?.health_score ?? "—"}%
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/3 border border-white/5">
                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Threat Level</span>
                <span className={cn(
                  "text-sm font-bold",
                  securityStatus?.threat_level === "CRITICAL" || securityStatus?.threat_level === "HIGH" ? "text-red-500" :
                  securityStatus?.threat_level === "MEDIUM" ? "text-amber-400" : "text-emerald-400"
                )}>
                  {securityStatus?.threat_level || "NOMINAL"}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/3 border border-white/5">
                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">System Integrity</span>
                <span className={cn(
                  "text-sm font-bold",
                  securityStatus?.system_integrity === "CRITICAL" ? "text-red-500" :
                  securityStatus?.system_integrity === "DEGRADED" ? "text-amber-400" : "text-emerald-400"
                )}>
                  {securityStatus?.system_integrity || "NOMINAL"}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-white/3 border border-white/5">
                <span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Security Events</span>
                <span className="text-sm font-bold text-white">{securityEvents?.length ?? 0}</span>
              </div>
            </div>
          </div>
          <button
            onClick={triggerAudit}
            disabled={isAuditing}
            className="w-full bg-cyan-500 hover:bg-cyan-400 text-white font-bold h-12 rounded-2xl transition-all flex items-center justify-center gap-2"
          >
            {isAuditing ? "Auditing..." : "Run New Audit"}
            <ArrowUpRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
