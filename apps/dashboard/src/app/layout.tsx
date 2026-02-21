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

import { AuthProvider } from "@/context/AuthContext";
import { UIProvider } from "@/context/UIContext";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans font-mono antialiased`}
      >
        <UIProvider>
          <AuthProvider>
            {children}
          </AuthProvider>
        </UIProvider>
      </body>
    </html>
  );
}
