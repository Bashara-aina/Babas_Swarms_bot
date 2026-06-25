"use client";

import { useCallback, useMemo, useState } from "react";
import type { AuditInput, AuditResult, OcrExtractedData, SlipGajiInput } from "@/types/slip";

type AuditApiResponse = AuditResult & {
  audit_id: string | null;
};

function toAuditInputFromManual(values: SlipGajiInput): AuditInput {
  return {
    gross: values.gaji_pokok + values.tunjangan_tetap + values.tunjangan_tidak_tetap,
    month: values.month,
    ptkp_status: values.ptkp_status,
    deductions: {
      pph21: values.pph21_charged,
      bpjs_kesehatan: values.bpjs_kesehatan_charged,
      bpjs_jht: values.bpjs_jht_charged,
      bpjs_jp: values.bpjs_jp_charged,
      bpjs_jkk: values.bpjs_jkk_charged ?? 0,
      bpjs_jkm: values.bpjs_jkm_charged ?? 0,
      potongan_lain: values.potongan_lain ?? 0
    }
  };
}

function toAuditInputFromOCR(data: OcrExtractedData, month: number, ptkp_status: SlipGajiInput["ptkp_status"]): AuditInput {
  const gajiPokok = data.gaji_pokok ?? 0;
  const tunjanganTetap = data.tunjangan_tetap ?? 0;
  const tunjanganTidakTetap = data.tunjangan_tidak_tetap ?? 0;

  return {
    gross: gajiPokok + tunjanganTetap + tunjanganTidakTetap,
    month,
    ptkp_status,
    deductions: {
      pph21: data.pph21 ?? 0,
      bpjs_kesehatan: data.bpjs_kesehatan ?? 0,
      bpjs_jht: data.bpjs_jht ?? 0,
      bpjs_jp: data.bpjs_jp ?? 0,
      bpjs_jkk: data.bpjs_jkk ?? 0,
      bpjs_jkm: data.bpjs_jkm ?? 0,
      potongan_lain: data.potongan_lain ?? 0
    }
  };
}

export function useAudit() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AuditApiResponse | null>(null);
  const [activeTab, setActiveTab] = useState<"manual" | "upload">("manual");
  const [ocrDraft, setOcrDraft] = useState<OcrExtractedData | null>(null);

  const submitAudit = useCallback(async (input: AuditInput): Promise<AuditApiResponse | null> => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch("/api/slip/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input)
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Gagal memproses audit");
      }
      const payload = (await response.json()) as AuditApiResponse;
      setResult(payload);
      return payload;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Terjadi kesalahan");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const submitManual = useCallback(
    async (form: SlipGajiInput): Promise<AuditApiResponse | null> => submitAudit(toAuditInputFromManual(form)),
    [submitAudit]
  );

  const submitOcr = useCallback(
    async (params: { data: OcrExtractedData; month: number; ptkp_status: SlipGajiInput["ptkp_status"] }) =>
      submitAudit(toAuditInputFromOCR(params.data, params.month, params.ptkp_status)),
    [submitAudit]
  );

  return useMemo(
    () => ({
      activeTab,
      setActiveTab,
      ocrDraft,
      setOcrDraft,
      submitAudit,
      submitManual,
      submitOcr,
      loading,
      error,
      result
    }),
    [activeTab, error, loading, ocrDraft, result, submitAudit, submitManual, submitOcr]
  );
}
