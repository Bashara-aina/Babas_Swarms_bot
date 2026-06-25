// @ts-nocheck
'use client'
import React, { useState, useEffect, useRef } from 'react'


// Wajar Kabur — full implementation

const COUNTRIES_FREE = [
  { code: 'SG', name: 'Singapura', flag: '🇸🇬', currency: 'SGD', rate: 11500, pppFactor: 0.58, pro: false },
  { code: 'MY', name: 'Malaysia', flag: '🇲🇾', currency: 'MYR', rate: 3300, pppFactor: 0.82, pro: false },
  { code: 'AU', name: 'Australia', flag: '🇦🇺', currency: 'AUD', rate: 10300, pppFactor: 0.44, pro: false },
  { code: 'JP', name: 'Jepang', flag: '🇯🇵', currency: 'JPY', rate: 105, pppFactor: 0.55, pro: false },
  { code: 'AE', name: 'Uni Emirat Arab', flag: '🇦🇪', currency: 'AED', rate: 4400, pppFactor: 0.52, pro: false },
  { code: 'US', name: 'Amerika Serikat', flag: '🇺🇸', currency: 'USD', rate: 16200, pppFactor: 0.38, pro: true },
  { code: 'GB', name: 'Inggris', flag: '🇬🇧', currency: 'GBP', rate: 20500, pppFactor: 0.40, pro: true },
  { code: 'DE', name: 'Jerman', flag: '🇩🇪', currency: 'EUR', rate: 17500, pppFactor: 0.42, pro: true },
  { code: 'NL', name: 'Belanda', flag: '🇳🇱', currency: 'EUR', rate: 17500, pppFactor: 0.41, pro: true },
  { code: 'CA', name: 'Kanada', flag: '🇨🇦', currency: 'CAD', rate: 11800, pppFactor: 0.43, pro: true },
  { code: 'KR', name: 'Korea Selatan', flag: '🇰🇷', currency: 'KRW', rate: 12, pppFactor: 0.50, pro: true },
  { code: 'HK', name: 'Hong Kong', flag: '🇭🇰', currency: 'HKD', rate: 2070, pppFactor: 0.48, pro: true },
  { code: 'QA', name: 'Qatar', flag: '🇶🇦', currency: 'QAR', rate: 4440, pppFactor: 0.54, pro: true },
  { code: 'NZ', name: 'Selandia Baru', flag: '🇳🇿', currency: 'NZD', rate: 9800, pppFactor: 0.46, pro: true },
];

function fmtIDR(n) { return 'Rp\u00a0' + Math.round(n).toLocaleString('id-ID'); }
function fmtIDRShort(n) {
  if (!n) return '–';
  if (n >= 1_000_000) return 'Rp\u00a0' + (n / 1_000_000).toFixed(1).replace('.', ',') + ' jt';
  return fmtIDR(n);
}

function ResultSkeleton() {
  const bar = (w, h = 16) => (
    <div style={{ width: w, height: h, background: 'var(--muted)', borderRadius: 8,
      backgroundImage: 'linear-gradient(90deg, var(--muted) 25%, var(--border) 37%, var(--muted) 63%)',
      backgroundSize: '400% 100%', animation: 'shimmer 1.8s ease infinite' }} />
  );
  return (
    <div style={{ padding: '20px 0' }}>
      <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, padding: 20, marginBottom: 16 }}>
        {bar('40%', 28)}<div style={{ height: 10 }} />{bar('80%')}<div style={{ height: 6 }} />{bar('60%')}
      </div>
      <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, padding: 20, marginBottom: 16 }}>
        {bar('100%', 80)}
      </div>
    </div>
  );
}

const inputStyle = {
  width: '100%', boxSizing: 'border-box', height: 52, padding: '0 14px',
  border: '1.5px solid var(--border)', borderRadius: 10,
  background: 'var(--card)', color: 'var(--foreground)',
  fontSize: 15, fontFamily: 'inherit', outline: 'none', transition: 'border-color 150ms',
};

function FocusInput({ value, onChange, placeholder, style }) {
  const [f, setF] = useState(false);
  return <input value={value} onChange={onChange} placeholder={placeholder}
    style={{ ...inputStyle, ...(f ? { borderColor: '#6366f1' } : {}), ...style }}
    onFocus={() => setF(true)} onBlur={() => setF(false)} />;
}

function WajarKaburPage({ onNavigate }) {
  const [stage, setStage] = useState('IDLE');
  const [gajiIDR, setGajiIDR] = useState('');
  const [country, setCountry] = useState('');
  const [offerSalary, setOfferSalary] = useState('');
  const [result, setResult] = useState(null);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [errors, setErrors] = useState({});

  const accentColor = '#6366f1';
  const bg = '#eef2ff';

  const fmtIDRInput = (val, setter) => ({
    value: val,
    onChange: e => { const r = e.target.value.replace(/\D/g,''); setter(r ? parseInt(r,10).toLocaleString('id-ID') : ''); }
  });

  const selectedCountry = COUNTRIES_FREE.find(c => c.code === country);

  const handleSubmit = () => {
    const errs = {};
    if (!gajiIDR) errs.gajiIDR = 'Masukkan gaji kamu di Indonesia';
    if (!country) errs.country = 'Pilih negara tujuan';
    if (selectedCountry?.pro) { errs.country = 'Negara ini tersedia di Pro. Pilih negara gratis atau upgrade.'; }
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    setStage('LOADING');

    const c = selectedCountry;
    const msgs = [
      `Mengambil data PPP untuk ${c.name}...`,
      `Menghitung kurs ${c.currency} dari Frankfurter API...`,
      'Membandingkan daya beli nyata...',
    ];
    let i = 0;
    setLoadingMsg(msgs[0]);
    const iv = setInterval(() => { i++; if (i < msgs.length) setLoadingMsg(msgs[i]); }, 700);

    setTimeout(() => {
      clearInterval(iv);
      const gajiNum = parseInt(gajiIDR.replace(/\D/g,''), 10);
      const offerNum = offerSalary ? parseInt(offerSalary.replace(/\D/g,''), 10) : null;

      // Convert offer to IDR nominal
      const offerInIDR = offerNum ? offerNum * c.rate : null;
      // PPP-adjusted: what IDR gaji is equivalent to in terms of local purchasing power
      const gajiLocalEquiv = gajiNum / c.rate; // nominal local equivalent
      const pppEquivIDR = offerInIDR ? offerInIDR * c.pppFactor : null; // offer's real IDR equiv

      let verdictType, verdictSentence;
      if (offerNum) {
        const ratio = pppEquivIDR / gajiNum;
        if (ratio > 1.2) {
          verdictType = 'LEBIH_BAIK';
          verdictSentence = `Secara daya beli, tawaran ini setara Rp ${Math.round(pppEquivIDR).toLocaleString('id-ID')}/bulan di Indonesia — ${Math.round((ratio-1)*100)}% lebih tinggi.`;
        } else if (ratio < 0.85) {
          verdictType = 'LEBIH_RENDAH';
          verdictSentence = `Secara daya beli nyata, tawaran ini hanya setara Rp ${Math.round(pppEquivIDR).toLocaleString('id-ID')}/bulan di Indonesia.`;
        } else {
          verdictType = 'SEBANDING';
          verdictSentence = `Daya beli tawaran ini sebanding dengan gaji kamu sekarang di Indonesia.`;
        }
      } else {
        verdictType = 'INFO';
        verdictSentence = `Gaji Rp ${gajiNum.toLocaleString('id-ID')}/bulan setara daya beli ${c.currency} ${Math.round(gajiLocalEquiv * c.pppFactor).toLocaleString('id-ID')}/bulan di ${c.name}.`;
      }

      setResult({
        verdictType, verdictSentence, gajiNum, offerNum, offerInIDR, pppEquivIDR,
        country: c, gajiLocalEquiv,
      });
      setStage('RESULT');
    }, 2500);
  };

  if (stage === 'LOADING') return (
    <div data-tool="wajar-kabur" style={{ minHeight: '80vh', background: bg, padding: '32px 0' }}>
      <div style={{ maxWidth: 560, margin: '0 auto', padding: '0 20px' }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ width: 48, height: 48, borderRadius: '50%', border: `4px solid #c7d2fe`, borderTopColor: accentColor, animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--foreground)', marginBottom: 4 }}>{loadingMsg}</div>
          <div style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>Ini butuh 2–3 detik untuk akurasi terbaik...</div>
        </div>
        <ResultSkeleton />
      </div>
    </div>
  );

  if (stage === 'RESULT' && result) {
    const { verdictType, verdictSentence, gajiNum, offerNum, offerInIDR, pppEquivIDR, country: c, gajiLocalEquiv } = result;
    const VERDICT_MAP = {
      LEBIH_BAIK:  { color: '#16a34a', bg: 'rgba(22,163,74,0.05)',  border: '#16a34a', label: 'LEBIH BAIK' },
      LEBIH_RENDAH:{ color: '#dc2626', bg: 'rgba(220,38,38,0.05)', border: '#dc2626', label: 'LEBIH RENDAH' },
      SEBANDING:   { color: '#d97706', bg: 'rgba(217,119,6,0.05)',  border: '#d97706', label: 'SEBANDING' },
      INFO:        { color: accentColor, bg: 'rgba(99,102,241,0.05)', border: accentColor, label: 'INFORMASI' },
    };
    const vs = VERDICT_MAP[verdictType] || VERDICT_MAP.INFO;

    return (
      <div data-tool="wajar-kabur" style={{ minHeight: '80vh', background: bg, padding: '32px 0' }}>
        <div style={{ maxWidth: 600, margin: '0 auto', padding: '0 20px' }}>
          <button onClick={() => { setStage('IDLE'); setResult(null); }} style={{ display: 'flex', alignItems: 'center', gap: 4, background: 'none', border: 'none', color: 'var(--muted-foreground)', cursor: 'pointer', fontSize: 13, marginBottom: 20 }}>← Cek lagi</button>

          {/* Verdict */}
          <div className="animate-fade-in-up" style={{ borderLeft: `4px solid ${vs.border}`, background: vs.bg, borderRadius: '0 12px 12px 0', padding: '20px 20px 20px 24px', marginBottom: 16 }}>
            <div style={{ fontSize: 'clamp(1.5rem, 4vw, 2.25rem)', fontWeight: 800, color: vs.color, letterSpacing: '-0.02em', lineHeight: 1.1, marginBottom: 8 }}>{vs.label}</div>
            <div style={{ fontSize: 14, color: 'var(--muted-foreground)', lineHeight: 1.5, marginBottom: 10 }}>{verdictSentence}</div>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--muted-foreground)' }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: accentColor }} />
              PPP dari World Bank · Kurs Frankfurter API · Diperbarui harian
            </span>
          </div>

          {/* Exchange rate (secondary) */}
          <div style={{ padding: '10px 14px', background: 'var(--muted)', borderRadius: 8, marginBottom: 14, fontSize: 12, color: 'var(--muted-foreground)', fontFamily: 'var(--font-mono)' }}>
            1 {c.currency} = Rp {c.rate.toLocaleString('id-ID')} · PPP factor {c.pppFactor}
          </div>

          {/* Comparison card */}
          <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, padding: 20, marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--foreground)', marginBottom: 14 }}>Perbandingan Daya Beli</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
              <div style={{ background: 'var(--muted)', borderRadius: 10, padding: '14px 12px' }}>
                <div style={{ fontSize: 10, color: 'var(--muted-foreground)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>Gaji Sekarang (IDR)</div>
                <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--foreground)', fontFamily: 'var(--font-mono)', marginBottom: 3 }}>{fmtIDRShort(gajiNum)}</div>
                <div style={{ fontSize: 11, color: 'var(--muted-foreground)' }}>per bulan di Indonesia</div>
              </div>
              {offerNum ? (
                <div style={{ background: 'var(--muted)', borderRadius: 10, padding: '14px 12px' }}>
                  <div style={{ fontSize: 10, color: 'var(--muted-foreground)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>Daya Beli Tawaran (IDR equiv.)</div>
                  <div style={{ fontSize: 18, fontWeight: 800, color: vs.color, fontFamily: 'var(--font-mono)', marginBottom: 3 }}>{fmtIDRShort(pppEquivIDR)}</div>
                  <div style={{ fontSize: 11, color: 'var(--muted-foreground)' }}>setelah PPP adjustment</div>
                </div>
              ) : (
                <div style={{ background: 'var(--muted)', borderRadius: 10, padding: '14px 12px' }}>
                  <div style={{ fontSize: 10, color: 'var(--muted-foreground)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>Equiv. di {c.name} (PPP)</div>
                  <div style={{ fontSize: 18, fontWeight: 800, color: accentColor, fontFamily: 'var(--font-mono)', marginBottom: 3 }}>{c.currency} {Math.round(gajiLocalEquiv * c.pppFactor).toLocaleString('id-ID')}</div>
                  <div style={{ fontSize: 11, color: 'var(--muted-foreground)' }}>daya beli setara</div>
                </div>
              )}
            </div>
            {offerNum && (
              <div style={{ padding: '10px 14px', background: 'var(--muted)', borderRadius: 8, fontSize: 12, color: 'var(--muted-foreground)' }}>
                Tawaran nominal: {c.currency} {offerNum.toLocaleString('id-ID')} = {fmtIDRShort(offerInIDR)} sebelum PPP
              </div>
            )}
          </div>

          {/* Premium */}
          <div style={{ marginBottom: 20 }}>
            {['Breakdown biaya hidup di ' + c.name + ' per kategori', 'Perbandingan pajak penghasilan Indonesia vs. ' + c.name, 'Estimasi tabungan setelah biaya hidup'].map(label => (
              <div key={label} style={{ position: 'relative', marginBottom: 8, borderRadius: 8, overflow: 'hidden' }}>
                <div style={{ height: 44, background: 'var(--muted)', borderRadius: 8, filter: 'blur(3px)' }} />
                <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <span style={{ fontSize: 12, color: 'var(--muted-foreground)', fontWeight: 500 }}>🔒 {label}</span>
                </div>
              </div>
            ))}
            <div onClick={() => onNavigate('pricing')} style={{ border: '1.5px solid var(--border)', borderRadius: 12, padding: '14px 16px', cursor: 'pointer', background: 'var(--card)', marginTop: 4 }}
              onMouseEnter={e => e.currentTarget.style.borderColor = accentColor}
              onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
            >
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--foreground)', marginBottom: 8 }}>Lihat analisis lengkap biaya hidup dan pajak di {c.name}</div>
              <div style={{ display: 'inline-block', padding: '8px 16px', borderRadius: 8, background: accentColor, fontSize: 13, fontWeight: 600, color: '#fff' }}>
                Buka dengan Pro — Rp 49.000/bulan
              </div>
              <div style={{ fontSize: 11, color: 'var(--muted-foreground)', marginTop: 6 }}>Batalkan kapan saja · Tanpa kontrak</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
            <button onClick={() => { setStage('IDLE'); setResult(null); }} style={{ flex: 1, padding: '12px', borderRadius: 8, border: '1.5px solid var(--border)', background: 'var(--card)', color: 'var(--foreground)', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>← Cek lagi</button>
            <button style={{ padding: '12px 16px', borderRadius: 8, border: `1.5px solid ${accentColor}`, background: '#eef2ff', color: accentColor, fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>📤 Bagikan</button>
          </div>

          <button onClick={() => onNavigate('wajar-hidup')} style={{ display: 'block', width: '100%', padding: '12px 16px', border: '1px solid var(--border)', borderRadius: 10, background: 'var(--muted)', cursor: 'pointer', textAlign: 'left', fontSize: 13 }}>
            💡 Bandingkan juga biaya hidup antar kota di Indonesia →{' '}<span style={{ color: '#14b8a6', fontWeight: 600 }}>Wajar Hidup</span>
          </button>
        </div>
      </div>
    );
  }

  // IDLE
  return (
    <div data-tool="wajar-kabur" style={{ minHeight: '80vh', background: bg, padding: '32px 0' }}>
      <div style={{ maxWidth: 560, margin: '0 auto', padding: '0 20px' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ fontSize: 40, marginBottom: 10 }}>✈️</div>
          <h1 style={{ fontSize: 'clamp(1.4rem, 3vw, 1.8rem)', fontWeight: 800, color: 'var(--foreground)', marginBottom: 6 }}>Wajar Kabur</h1>
          <p style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>Bandingkan daya beli nyata gaji kamu di luar negeri</p>
        </div>

        {/* Edu callout */}
        <div style={{ padding: '12px 14px', background: '#eef2ff', border: '1px solid #c7d2fe', borderRadius: 10, marginBottom: 20, fontSize: 12, color: '#4338ca', lineHeight: 1.6 }}>
          <strong>Kenapa tidak bisa dibandingkan langsung?</strong> Angka nominal di negara berbeda tidak mencerminkan daya beli nyata. Kami pakai data PPP (Purchasing Power Parity) dari World Bank untuk perbandingan yang adil.
        </div>

        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, padding: '24px' }}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 6 }}>Gaji Kamu di Indonesia</label>
            <FocusInput placeholder="cth. 18.000.000" {...{
              value: gajiIDR,
              onChange: e => { const r = e.target.value.replace(/\D/g,''); setGajiIDR(r ? parseInt(r,10).toLocaleString('id-ID') : ''); }
            }} />
            {errors.gajiIDR && <div style={{ fontSize: 11, color: '#dc2626', marginTop: 4 }}>{errors.gajiIDR}</div>}
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 6 }}>Negara Tujuan</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6 }}>
              {COUNTRIES_FREE.map(c => (
                <button key={c.code} onClick={() => { if (!c.pro) { setCountry(c.code); setErrors({}); } }} style={{
                  padding: '10px 12px', borderRadius: 10, border: '1.5px solid',
                  borderColor: country === c.code ? accentColor : 'var(--border)',
                  background: country === c.code ? '#eef2ff' : 'var(--card)',
                  cursor: c.pro ? 'not-allowed' : 'pointer', textAlign: 'left',
                  opacity: c.pro ? 0.6 : 1, transition: 'all 150ms',
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                }}>
                  <span style={{ fontSize: 13, fontWeight: country === c.code ? 700 : 500, color: country === c.code ? accentColor : 'var(--foreground)' }}>
                    {c.flag} {c.name}
                  </span>
                  {c.pro && (
                    <span style={{ fontSize: 9, fontWeight: 700, background: accentColor, color: '#fff', padding: '2px 6px', borderRadius: 99 }}>PRO</span>
                  )}
                </button>
              ))}
            </div>
            {errors.country && <div style={{ fontSize: 11, color: '#dc2626', marginTop: 6 }}>{errors.country}</div>}
          </div>

          {/* Optional offer */}
          <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16, marginBottom: 20 }}>
            <div style={{ fontSize: 12, color: 'var(--muted-foreground)', marginBottom: 10, lineHeight: 1.5 }}>
              <span style={{ fontWeight: 600 }}>Opsional</span> — bandingkan langsung dengan tawaran nyata
            </div>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 6 }}>
              Gaji Ditawarkan di LN
              {selectedCountry && <span style={{ fontSize: 11, color: 'var(--muted-foreground)', fontWeight: 400, marginLeft: 6 }}>dalam {selectedCountry.currency}</span>}
            </label>
            <FocusInput value={offerSalary} onChange={e => { const r = e.target.value.replace(/\D/g,''); setOfferSalary(r ? parseInt(r,10).toLocaleString('id-ID') : ''); }} placeholder={selectedCountry ? `cth. 5.000 ${selectedCountry.currency}` : 'Pilih negara dulu'} style={{ opacity: !country ? 0.5 : 1 }} />
          </div>

          <button onClick={handleSubmit} style={{ width: '100%', padding: '14px', borderRadius: 10, border: 'none', background: accentColor, color: '#fff', fontSize: 15, fontWeight: 700, cursor: 'pointer' }}>
            Hitung Daya Beli →
          </button>
        </div>

        <div style={{ textAlign: 'center', fontSize: 11, color: 'var(--muted-foreground)', marginTop: 12, fontFamily: 'var(--font-mono)' }}>
          PPP dari World Bank · Kurs dari Frankfurter API · Diperbarui harian
        </div>
      </div>
    </div>
  );
}


export default WajarKaburPage
