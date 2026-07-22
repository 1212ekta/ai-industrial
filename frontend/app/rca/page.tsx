"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Database, AlertTriangle, Target, Search } from "lucide-react";
import api from "@/lib/api";
import { motion, AnimatePresence } from "framer-motion";

export default function RCAPage() {
  const [equipment, setEquipment] = useState("");
  const [problem, setProblem] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleAnalyze = async () => {
    if (!equipment || !problem) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await api.post("/rca", { equipment, problem_description: problem });
      setResult(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 mt-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Root Cause Analysis</h1>
      </div>

      <Card className="border-border/50 bg-card shadow-sm">
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-medium">Equipment Name / ID</label>
              <Input 
                placeholder="e.g. Pump P-102A" 
                value={equipment}
                onChange={e => setEquipment(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Problem Description</label>
              <Input 
                placeholder="e.g. High vibration during startup" 
                value={problem}
                onChange={e => setProblem(e.target.value)}
              />
            </div>
          </div>
          <Button 
            className="mt-6 w-full md:w-auto" 
            onClick={handleAnalyze}
            disabled={loading || !equipment || !problem}
          >
            <Search className="mr-2 h-4 w-4" />
            {loading ? "Analyzing Context..." : "Run AI Analysis"}
          </Button>
        </CardContent>
      </Card>

      <AnimatePresence>
        {result && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-1 md:grid-cols-2 gap-6"
          >
            {/* Likely Causes */}
            <Card className="border-border/50 bg-accent/10">
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <AlertTriangle className="mr-2 h-5 w-5 text-orange-500" />
                  Likely Causes
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {result.likely_causes?.map((cause: any, i: number) => (
                  <div key={i} className="flex items-center justify-between">
                    <span className="text-sm font-medium">{cause.cause}</span>
                    <div className="flex items-center space-x-2">
                      <div className="w-24 h-2 bg-accent rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-orange-500" 
                          style={{ width: `${cause.probability * 100}%` }}
                        />
                      </div>
                      <span className="text-xs font-bold text-muted-foreground w-8 text-right">
                        {Math.round(cause.probability * 100)}%
                      </span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Recommendations */}
            <Card className="border-border/50 bg-accent/10">
              <CardHeader>
                <CardTitle className="text-lg flex items-center">
                  <Target className="mr-2 h-5 w-5 text-green-500" />
                  Recommended Actions
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {result.recommendations?.map((rec: string, i: number) => (
                    <li key={i} className="flex items-start space-x-2 text-sm">
                      <span className="flex-shrink-0 w-5 h-5 rounded-full bg-green-500/20 text-green-500 flex items-center justify-center text-xs font-bold mt-0.5">
                        {i + 1}
                      </span>
                      <span className="text-muted-foreground">{rec}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
