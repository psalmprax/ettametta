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

import RootClientContext from "@/components/providers/RootClientContext";

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
        <RootClientContext>
          {children}
        </RootClientContext>
      </body>
    </html>
  );
}
