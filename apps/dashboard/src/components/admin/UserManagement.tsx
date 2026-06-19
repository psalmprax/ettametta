"use client";

import React from "react";

export default function UserManagement() {
  return (
    <div className="space-y-8">
      <h3 className="text-2xl font-bold text-white uppercase tracking-widest">User Management</h3>
      <div className="p-8 rounded-[32px] bg-[#0F0F11]/60 border border-white/5 text-center">
        <p className="text-xs font-bold text-zinc-600 uppercase tracking-wider">No user management features configured</p>
        <p className="text-[9px] text-zinc-700 mt-1">User admin panel will be available when user directory is enabled</p>
      </div>
    </div>
  );
}
