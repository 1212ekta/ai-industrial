"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, Settings, AlertTriangle, CloudUpload } from "lucide-react";
import api from "@/lib/api";
import { motion } from "framer-motion";

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    api.get("/dashboard").then(res => setStats(res.data)).catch(console.error);
  }, []);

  if (!stats) {
    return <div className="flex h-full items-center justify-center text-muted-foreground animate-pulse">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Overview</h1>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard title="Total Documents" value={stats.total_documents} icon={<FileText className="h-6 w-6 text-blue-500" />} delay={0.1} />
        <StatCard title="Equipment Entities" value={stats.equipment_count} icon={<Settings className="h-6 w-6 text-green-500" />} delay={0.2} />
        <StatCard title="Known Failures" value={stats.failures_count} icon={<AlertTriangle className="h-6 w-6 text-orange-500" />} delay={0.3} />
        <StatCard title="Active Queries" value={12} icon={<CloudUpload className="h-6 w-6 text-purple-500" />} delay={0.4} />
      </div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.recent_uploads?.map((doc: any) => (
                <div key={doc.id} className="flex items-center justify-between border-b border-border/50 pb-4 last:border-0 last:pb-0">
                  <div>
                    <p className="text-sm font-medium">{doc.filename}</p>
                    <p className="text-xs text-muted-foreground">{new Date(doc.upload_date).toLocaleString()}</p>
                  </div>
                  <div className="text-sm px-2 py-1 bg-primary/20 text-primary rounded-full">
                    {doc.status}
                  </div>
                </div>
              ))}
              {(!stats.recent_uploads || stats.recent_uploads.length === 0) && (
                <p className="text-sm text-muted-foreground">No recent activity.</p>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}

function StatCard({ title, value, icon, delay }: any) {
  return (
    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay, duration: 0.3 }}>
      <Card className="border-border/50 bg-card hover:border-border transition-colors">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
          {icon}
        </CardHeader>
        <CardContent>
          <div className="text-3xl font-bold">{value}</div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
