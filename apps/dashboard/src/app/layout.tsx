import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ettametta | Autonomous Social Engine",
  description: "Next-generation generative social distribution network.",
};

import dynamic from "next/dynamic";

// Lazy load heavy components for better performance
const AuthProvider = dynamic(() => import("@/context/AuthContext").then(mod => ({ default: mod.AuthProvider })), {
  ssr: false, // Client-side only for auth
});

const UIProvider = dynamic(() => import("@/context/UIContext").then(mod => ({ default: mod.UIProvider })), {
  ssr: false,
});

const UIThemeProvider = dynamic(() => import("@/context/UIThemeContext").then(mod => ({ default: mod.UIThemeProvider })), {
  ssr: false,
});

const QueryProvider = dynamic(() => import("@/components/providers/QueryProvider"), {
  ssr: false, // QueryClient needs client-side
});

const GlobalErrorBoundary = dynamic(() => import("@/components/GlobalErrorBoundary"));
const Toaster = dynamic(() => import("sonner").then(mod => ({ default: mod.Toaster })), {
  ssr: false,
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans font-mono antialiased relative`}
      >
        <div className="ambient-mesh" />
        <QueryProvider>
          <UIThemeProvider>
            <UIProvider>
              <AuthProvider>
                <GlobalErrorBoundary>
                  {children}
                </GlobalErrorBoundary>
              </AuthProvider>
            </UIProvider>
          </UIThemeProvider>
        </QueryProvider>
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
      </body>
    </html>
  );
}
