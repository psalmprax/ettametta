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
  title: "Ettametta | Autonomous Viral Content Intelligence",
  description: "Discover, transform, and dominate every feed with AI-powered content discovery, synthesis, and autonomous multi-platform publishing.",
};

import RootClientContext from "@/components/providers/RootClientContext";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <script dangerouslySetInnerHTML={{ __html: `
          (function() {
            // Polyfill crypto.randomUUID for older browsers
            if (typeof crypto !== 'undefined' && !crypto.randomUUID) {
              crypto.randomUUID = function() {
                return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                  var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                  return v.toString(16);
                });
              };
            }

            // Suppress known spurious console errors from third-party scripts
            // (e.g., platform-injected push notification scripts, CDN scripts)
            // Uses specific error message substrings to avoid hiding legitimate errors.
            var KEYS = ['error subscribing to push notifications', 'err_connection_timed_out'];
            var origError = console.error;
            console.error = function() {
              var msg = Array.prototype.join.call(arguments, ' ').toLowerCase();
              for (var i = 0; i < KEYS.length; i++) {
                if (msg.indexOf(KEYS[i]) !== -1) return;
              }
              return origError.apply(console, arguments);
            };

            // Catch unhandled promise rejections and error events from third-party scripts
            window.addEventListener('unhandledrejection', function(e) {
              var msg = String(e.reason).toLowerCase();
              for (var i = 0; i < KEYS.length; i++) {
                if (msg.indexOf(KEYS[i]) !== -1) {
                  e.preventDefault();
                  return;
                }
              }
            });

            window.addEventListener('error', function(e) {
              var msg = String(e.error || e.message || '').toLowerCase();
              for (var i = 0; i < KEYS.length; i++) {
                if (msg.indexOf(KEYS[i]) !== -1) {
                  e.preventDefault();
                  return;
                }
              }
            });
          })();
        ` }} />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans font-mono antialiased relative`}
      >
        <div className="ambient-mesh" />
        <RootClientContext>
          {children}
        </RootClientContext>
      </body>
    </html>
  );
}
