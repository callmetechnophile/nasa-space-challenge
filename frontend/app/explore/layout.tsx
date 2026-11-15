import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "SkyTrace",
  description: "A scientific astronomy development environment for exploring and analyzing SPHEREx observations.",
};

export default function ExploreLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
