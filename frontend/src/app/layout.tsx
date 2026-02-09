import type { Metadata } from "next";
import { Outfit, Great_Vibes } from "next/font/google";
import { GlobalHeader } from "@/components/GlobalHeader";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  weight: ["200", "300", "400", "500", "600", "700"],
});

const greatVibes = Great_Vibes({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-great-vibes",
});

export const metadata: Metadata = {
  title: "Galileo Arena",
  description: "Multi-model agentic debate evaluation platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className={`${outfit.className} ${greatVibes.variable} min-h-screen antialiased relative`} suppressHydrationWarning>
        <GlobalHeader />
        {children}
      </body>
    </html>
  );
}
