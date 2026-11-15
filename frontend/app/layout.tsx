import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import localFont from "next/font/local";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const corpta = localFont({
  src: "../public/fonts/corpta.otf",
  variable: "--font-corpta",
  display: "swap",
});

const aeruno = localFont({
  src: "../public/fonts/aeruno.otf",
  variable: "--font-aeruno",
  display: "swap",
});

export const metadata: Metadata = {
  title: "SkyTrace",
  description:
    "An interactive scientific environment for exploring the infrared sky, examining observations across time, and investigating the spectral signatures hidden within SPHEREx astronomical data.",
  openGraph: {
    title: "SkyTrace",
    description:
      "An interactive scientific environment for exploring the infrared sky, examining observations across time, and investigating the spectral signatures hidden within SPHEREx astronomical data.",
    siteName: "SkyTrace",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} ${corpta.variable} ${aeruno.variable} h-full dark antialiased scroll-smooth`}
    >
      <body className="min-h-full w-full bg-[#02040a] text-slate-100 font-sans selection:bg-cyan-500/30 selection:text-cyan-100">
        {children}
      </body>
    </html>
  );
}
