import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";
import { Database, FileText, Activity, LayoutDashboard, BrainCircuit, Share2 } from "lucide-react";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "IKIP - Industrial Knowledge Intelligence",
  description: "Enterprise Industrial AI Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-background text-foreground flex h-screen overflow-hidden`}>
        {/* Sidebar */}
        <aside className="w-64 border-r border-border bg-card flex flex-col h-full">
          <div className="p-6 border-b border-border flex items-center space-x-3">
            <BrainCircuit className="h-8 w-8 text-primary" />
            <span className="font-bold text-xl tracking-tight">IKIP AI</span>
          </div>
          <nav className="flex-1 overflow-y-auto p-4 space-y-2">
            <NavItem href="/" icon={<LayoutDashboard className="h-5 w-5" />} label="Dashboard" />
            <NavItem href="/upload" icon={<Activity className="h-5 w-5" />} label="Upload" />
            <NavItem href="/library" icon={<FileText className="h-5 w-5" />} label="Library" />
            <NavItem href="/graph" icon={<Share2 className="h-5 w-5" />} label="Knowledge Graph" />
            <NavItem href="/copilot" icon={<BrainCircuit className="h-5 w-5" />} label="AI Copilot" />
            <NavItem href="/rca" icon={<Database className="h-5 w-5" />} label="Root Cause Analysis" />
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <header className="h-16 border-b border-border flex items-center px-6 justify-between bg-card">
            <h2 className="text-lg font-medium">Enterprise Workspace</h2>
            <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold text-sm">
              AD
            </div>
          </header>
          <div className="flex-1 overflow-auto p-6 bg-background">
            {children}
          </div>
        </main>
      </body>
    </html>
  );
}

function NavItem({ href, icon, label }: { href: string; icon: React.ReactNode; label: string }) {
  return (
    <Link href={href} className="flex items-center space-x-3 px-3 py-2.5 rounded-lg text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-all">
      {icon}
      <span className="font-medium text-sm">{label}</span>
    </Link>
  );
}
