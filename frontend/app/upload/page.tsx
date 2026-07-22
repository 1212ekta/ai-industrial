"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { UploadCloud, CheckCircle2, AlertCircle } from "lucide-react";
import api from "@/lib/api";
import { motion } from "framer-motion";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "success" | "error">("idle");

  const handleUpload = async () => {
    if (!file) return;
    setStatus("uploading");
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      await api.post("/documents/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });
      setStatus("success");
      setFile(null);
    } catch (err) {
      console.error(err);
      setStatus("error");
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 mt-10">
      <h1 className="text-3xl font-bold tracking-tight">Upload Documents</h1>
      <p className="text-muted-foreground">Upload industrial manuals, inspection reports, and logs to the AI knowledge base.</p>

      <Card className="border-2 border-dashed border-border/50 bg-card/50">
        <CardContent className="flex flex-col items-center justify-center py-20 space-y-4">
          <UploadCloud className="h-12 w-12 text-muted-foreground" />
          <h3 className="text-lg font-medium">Drag & Drop or Click to Browse</h3>
          <p className="text-sm text-muted-foreground">Supports PDF, DOCX, TXT, Excel, PNG, JPG.</p>
          
          <input 
            type="file" 
            className="hidden" 
            id="file-upload" 
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
          <label htmlFor="file-upload">
            <Button variant="outline" className="mt-4" onClick={() => document.getElementById('file-upload')?.click()}>
              Select File
            </Button>
          </label>
        </CardContent>
      </Card>

      {file && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">Selected File</CardTitle>
            </CardHeader>
            <CardContent className="flex items-center justify-between">
              <span className="font-medium text-sm">{file.name}</span>
              <Button onClick={handleUpload} disabled={status === "uploading"}>
                {status === "uploading" ? "Uploading..." : "Upload File"}
              </Button>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {status === "success" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center space-x-2 text-green-500 bg-green-500/10 p-4 rounded-lg">
          <CheckCircle2 className="h-5 w-5" />
          <span className="font-medium text-sm">File uploaded successfully! Background processing started.</span>
        </motion.div>
      )}

      {status === "error" && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center space-x-2 text-red-500 bg-red-500/10 p-4 rounded-lg">
          <AlertCircle className="h-5 w-5" />
          <span className="font-medium text-sm">Failed to upload file. Please try again.</span>
        </motion.div>
      )}
    </div>
  );
}
