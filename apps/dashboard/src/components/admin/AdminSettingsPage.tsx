"use client";

import React from "react";
import { SettingField } from "./SharedComponents";

export default function AdminSettingsPage({ settings, setSettings }: { readonly settings: any, readonly setSettings: (s: any) => void }) {
  return (
    <div className="space-y-10">
      <div className="space-y-8">
        <h3 className="text-2xl font-bold text-white uppercase tracking-widest">OAuth Configuration</h3>
        <div className="grid grid-cols-1 gap-6">
          <SettingField label="Google Client ID" value={settings.google_client_id} onChange={(v) => setSettings({...settings, google_client_id: v})} />
          <SettingField label="Google Secret" value={settings.google_client_secret} onChange={(v) => setSettings({...settings, google_client_secret: v})} isSecret />
          <SettingField label="TikTok Key" value={settings.tiktok_client_key} onChange={(v) => setSettings({...settings, tiktok_client_key: v})} />
          <SettingField label="TikTok Secret" value={settings.tiktok_client_secret} onChange={(v) => setSettings({...settings, tiktok_client_secret: v})} isSecret />
        </div>
      </div>
    </div>
  );
}

export function InfrastructureSettings({ settings, setSettings }: { readonly settings: any, readonly setSettings: (s: any) => void }) {
  return (
    <div className="p-10 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 space-y-6">
      <SettingField label="Production Domain" value={settings.production_domain} onChange={(v) => setSettings({...settings, production_domain: v})} />
      <SettingField label="Render Cluster URL" value={settings.render_node_url} onChange={(v) => setSettings({...settings, render_node_url: v})} />
    </div>
  );
}
