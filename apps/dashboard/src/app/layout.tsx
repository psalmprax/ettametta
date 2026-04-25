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
            if (typeof crypto !== 'undefined' && !crypto.randomUUID) {
              crypto.randomUUID = function() {
                return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                  var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                  return v.toString(16);
                });
              };
            }
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
