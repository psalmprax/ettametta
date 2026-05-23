'use client';

import '@/lib/react-polyfill';
import React from 'react';
import { AuthProvider } from '@/context/AuthContext';
import { UIProvider } from '@/context/UIContext';
import { UIThemeProvider } from '@/context/UIThemeContext';
import QueryProvider from '@/components/providers/QueryProvider';
import GlobalErrorBoundary from '@/components/GlobalErrorBoundary';
import { TelemetryProvider } from '@/context/TelemetryContext';
import { Toaster } from 'sonner';

export default function RootClientContext({ children }: { readonly children: React.ReactNode }) {
  return (
    <QueryProvider>
      <UIThemeProvider>
        <UIProvider>
          <AuthProvider>
            <TelemetryProvider>
              <GlobalErrorBoundary>
                {children}
              </GlobalErrorBoundary>
            </TelemetryProvider>
            <Toaster
              theme="dark"
              position="top-right"
              toastOptions={{
                style: {
                  background: "rgba(9, 9, 11, 0.95)",
                  border: "1px solid rgba(255,255,255,0.08)",
                  backdropFilter: "blur(12px)",
                  color: "#fff",
                  fontWeight: 700,
                  fontSize: "12px",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                },
              }}
            />
          </AuthProvider>
        </UIProvider>
      </UIThemeProvider>
    </QueryProvider>
  );
}
