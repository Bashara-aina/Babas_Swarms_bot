"use client";

import { useCallback, useEffect, useState } from "react";

type SnapStatus = "idle" | "pending" | "success" | "error";

type PaymentPayload = {
  audit_id: string;
  user_id?: string;
};

type UsePaymentOptions = {
  onSuccess?: () => void;
  onError?: (message: string) => void;
};

declare global {
  interface Window {
    snap?: {
      pay: (
        token: string,
        callbacks: {
          onSuccess?: () => void;
          onPending?: () => void;
          onError?: () => void;
          onClose?: () => void;
        }
      ) => void;
    };
  }
}

function snapScriptUrl(): string {
  return process.env.MIDTRANS_SANDBOX === "true"
    ? "https://app.sandbox.midtrans.com/snap/snap.js"
    : "https://app.midtrans.com/snap/snap.js";
}

export function usePayment(options?: UsePaymentOptions) {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<SnapStatus>("idle");

  useEffect(() => {
    const scriptId = "midtrans-snap-script";
    const existing = document.getElementById(scriptId);
    if (existing) return;

    const script = document.createElement("script");
    script.id = scriptId;
    script.src = snapScriptUrl();
    script.async = true;
    script.setAttribute("data-client-key", process.env.NEXT_PUBLIC_MIDTRANS_CLIENT_KEY ?? "");
    document.body.appendChild(script);
  }, []);

  const openSnap = useCallback(
    async (payload: PaymentPayload) => {
      try {
        setLoading(true);
        setStatus("idle");
        const response = await fetch("/api/payment/create-transaction", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });

        if (!response.ok) {
          const text = await response.text();
          throw new Error(text || "Failed to create transaction");
        }
        const data = (await response.json()) as { token: string };
        if (!window.snap || !data.token) {
          throw new Error("Snap.js not ready");
        }

        window.snap.pay(data.token, {
          onSuccess: () => {
            setStatus("success");
            setLoading(false);
            options?.onSuccess?.();
          },
          onPending: () => {
            setStatus("pending");
            setLoading(false);
          },
          onError: () => {
            setStatus("error");
            setLoading(false);
            options?.onError?.("Midtrans returned error");
          },
          onClose: () => {
            setLoading(false);
          }
        });
      } catch (error) {
        setStatus("error");
        setLoading(false);
        options?.onError?.(error instanceof Error ? error.message : "Unknown payment error");
      }
    },
    [options]
  );

  return { openSnap, loading, status };
}
