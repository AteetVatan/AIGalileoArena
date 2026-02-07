import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Galileo Arena",
  description: "Multi-model agentic debate evaluation platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className} suppressHydrationWarning>
        <nav className="border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 py-3 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <Link href="/" className="text-xl font-bold tracking-tight text-cyan-400 hover:text-cyan-300">
              Galileo Arena
            </Link>
            <div className="flex gap-6 text-sm text-slate-400">
              <Link href="/datasets" className="hover:text-white transition">Datasets</Link>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
