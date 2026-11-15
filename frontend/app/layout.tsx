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
  title: "SPHEREx | 3D Sky Explorer | DEMONSTRATION MODE",
  description:
    "Interactive 3D celestial sphere and procedural star field visualization for SPHEREx — Milestone 1.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full dark antialiased`}
    >
      <body className="h-full w-full bg-[#02040a] text-slate-100 overflow-hidden flex flex-col font-sans select-none">
        {children}
      </body>
    </html>
  );
}
