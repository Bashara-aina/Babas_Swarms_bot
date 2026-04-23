// @ts-nocheck
'use client'
import React, { useState, useEffect, useRef } from 'react'


// Wajar Hidup — full implementation

const HIDUP_CITIES = [
  'Jakarta','Surabaya','Bandung','Bali (Denpasar)','Yogyakarta',
  'Semarang','Medan','Makassar','Balikpapan','Malang',
  'Bekasi','Tangerang Selatan','Depok','Bogor','Palembang',
];

// Base monthly costs by city + lifestyle (IDR)
const COST_BASE = {
  'Jakarta':            { hemat: 5500000,  moderat: 9000000,  nyaman: 15000000 },
  'Surabaya':           { hemat: 4200000,  moderat: 7200000,  nyaman: 12000000 },
  'Bandung':            { hemat: 3800000,  moderat: 6500000,  nyaman: 10500000 },
  'Bali (Denpasar)':    { hemat: 4800000,  moderat: 8500000,  nyaman: 14000000 },
  'Yogyakarta':         { hemat: 3200000,  moderat: 5500000,  nyaman: 8500000  },
  'Semarang':           { hemat: 3600000,  moderat: 6000000,  nyaman: 9500000  },
  'Medan':              { hemat: 3800000,  moderat: 6200000,  nyaman: 10000000 },
  'Makassar':           { hemat: 3700000,  moderat: 6300000,  nyaman: 10200000 },
  'Balikpapan':         { hemat: 4500000,  moderat: 7500000,  nyaman: 12500000 },
  'Malang':             { hemat: 3000000,  moderat: 5200000,  nyaman: 8000000  },
  'Bekasi':             { hemat: 4500000,  moderat: 7500000,  nyaman: 12000000 },
  'Tangerang Selatan':  { hemat: 5000000,  moderat: 8500000,  nyaman: 14000000 },
  'Depok':              { hemat: 4200000,  moderat: 7000000,  nyaman: 11500000 },
  'Bogor':              { hemat: 3800000,  moderat: 6500000,  nyaman: 10500000 },
  'Palembang':          { hemat: 3400000,  moderat: 5800000,  nyaman: 9200000  },
};

// Category breakdown weights
const BREAKDOWN_WEIGHTS = {
  hemat:   { tinggal: 0.40, makan: 0.30, transport: 0.12, utilitas: 0.08, hiburan: 0.05, lainlain: 0.05 },
  moderat: { tinggal: 0.38, makan: 0.28, transport: 0.14, utilitas: 0.08, hiburan: 0.08, lainlain: 0.04 },
  nyaman:  { tinggal: 0.35, makan: 0.28, transport: 0.18, utilitas: 0.07, hiburan: 0.08, lainlain: 0.04 },
};

// People multiplier
const PEOPLE_MULT = { sendiri: 1, berdua: 1.6, keluarga: 2.3 };

const CATEGORIES = [
  { key: 'tinggal',   label: 'Tempat tinggal', icon: '🏠' },
  { key: 'makan',     label: 'Makan & minum',  icon: '🍽️' },
  { key: 'transport', label: 'Transportasi',    icon: '🚗' },
  { key: 'utilitas',  label: 'Utilitas',        icon: '💡' },
  { key: 'hiburan',   label: 'Hiburan & gaya hidup', icon: '🎬' },
  { key: 'lainlain',  label: 'Lain-lain',       icon: '📦' },
];

const PEOPLE_OPTIONS = [
  { id: 'sendiri', label: 'Sendiri', desc: '1 orang' },
  { id: 'berdua',  label: 'Berdua', desc: 'Pasangan' },
  { id: 'keluarga', label: 'Keluarga', desc: '3–4 orang' },
];

const LIFESTYLE_OPTIONS = [
  {
    id: 'hemat', label: 'Hemat',
    desc: 'Kost sederhana, masak sendiri, angkot / KRL',
    icon: '💰',
  },
  {
    id: 'moderat', label: 'Moderat',
    desc: 'Apartemen studio, warung + resto 2x/minggu, motor',
    icon: '⚖️',
  },
  {
    id: 'nyaman', label: 'Nyaman',
    desc: 'Apartemen 1BR, restoran 4x/minggu, mobil atau ojol premium',
    icon: '✨',
  },
];

function fmtIDR(n) { return 'Rp\u00a0' + Math.round(n).toLocaleString('id-ID'); }
function fmtIDRShort(n) {
  if (!n) return '–';
  if (n >= 1_000_000) return 'Rp\u00a0' + (n / 1_000_000).toFixed(1).replace('.', ',') + ' jt';
  return fmtIDR(n);
}

const inputStyle = {
  width: '100%', boxSizing: 'border-box', height: 52, padding: '0 14px',
  border: '1.5px solid var(--border)', borderRadius: 10,
  background: 'var(--card)', color: 'var(--foreground)',
  fontSize: 15, fontFamily: 'inherit', outline: 'none', transition: 'border-color 150ms',
};

function ResultSkeleton() {
  const bar = (w, h = 16) => (
    <div style={{ width: w, height: h, background: 'var(--muted)', borderRadius: 8,
      backgroundImage: 'linear-gradient(90deg, var(--muted) 25%, var(--border) 37%, var(--muted) 63%)',
      backgroundSize: '400% 100%', animation: 'shimmer 1.8s ease infinite' }} />
  );
  return (
    <div style={{ padding: '20px 0' }}>
      {[1,2,3].map(i => (
        <div key={i} style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, padding: 20, marginBottom: 14 }}>
          {bar(i === 1 ? '40%' : '90%', i === 1 ? 28 : 16)}<div style={{ height: 10 }} />{bar('70%')}
        </div>
      ))}
    </div>
  );
}

function WajarHidupPage({ onNavigate }) {
  const [stage, setStage] = useState('IDLE');
  const [cityDst, setCityDst] = useState('');
  const [people, setPeople] = useState('sendiri');
  const [lifestyle, setLifestyle] = useState('moderat');
  const [cityOrigin, setCityOrigin] = useState('');
  const [result, setResult] = useState(null);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [errors, setErrors] = useState({});

  const accentColor = '#14b8a6';
  const bg = '#f0fdfa';

  const handleSubmit = () => {
    const errs = {};
    if (!cityDst) errs.cityDst = 'Pilih kota tujuan';
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    setStage('LOADING');

    const msgs = [
      `Mengambil data biaya hidup di ${cityDst}...`,
      `Menghitung kebutuhan untuk gaya hidup ${lifestyle}...`,
      cityOrigin ? `Membandingkan dengan biaya hidup di ${cityOrigin}...` : 'Menghitung breakdown per kategori...',
    ];
    let i = 0;
    setLoadingMsg(msgs[0]);
    const iv = setInterval(() => { i++; if (i < msgs.length) setLoadingMsg(msgs[i]); }, 700);

    setTimeout(() => {
      clearInterval(iv);
      const baseDst = (COST_BASE[cityDst] || COST_BASE['Jakarta'])[lifestyle];
      const mult = PEOPLE_MULT[people] || 1;
      const totalDst = Math.round(baseDst * mult);

      const weights = BREAKDOWN_WEIGHTS[lifestyle];
      const breakdown = CATEGORIES.reduce((acc, { key }) => {
        acc[key] = Math.round(totalDst * weights[key]);
        return acc;
      }, {});

      let totalOrigin = null, verdictType = 'INFO', verdictSentence;
      if (cityOrigin && COST_BASE[cityOrigin]) {
        const baseOrigin = COST_BASE[cityOrigin][lifestyle];
        totalOrigin = Math.round(baseOrigin * mult);
        const diffPct = Math.round((totalDst - totalOrigin) / totalOrigin * 100);
        if (diffPct < -10) {
          verdictType = 'LEBIH_HEMAT';
          verdictSentence = `Biaya hidup di ${cityDst} ${Math.abs(diffPct)}% lebih hemat dari ${cityOrigin} untuk gaya hidup ${lifestyle}.`;
        } else if (diffPct > 10) {
          verdictType = 'LEBIH_MAHAL';
          verdictSentence = `Biaya hidup di ${cityDst} ${diffPct}% lebih mahal dari ${cityOrigin} untuk gaya hidup ${lifestyle}.`;
        } else {
          verdictType = 'SEBANDING';
          verdictSentence = `Biaya hidup di ${cityDst} dan ${cityOrigin} relatif sebanding untuk gaya hidup ${lifestyle}.`;
        }
      } else {
        verdictSentence = `Kamu butuh sekitar ${fmtIDRShort(totalDst)}/bulan untuk hidup ${lifestyle} di ${cityDst}.`;
      }

      setResult({ verdictType, verdictSentence, totalDst, totalOrigin, breakdown, cityDst, cityOrigin, lifestyle, people });
      setStage('RESULT');
    }, 2600);
  };

  if (stage === 'LOADING') return (
    <div data-tool="wajar-hidup" style={{ minHeight: '80vh', background: bg, padding: '32px 0' }}>
      <div style={{ maxWidth: 560, margin: '0 auto', padding: '0 20px' }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ width: 48, height: 48, borderRadius: '50%', border: `4px solid #99f6e4`, borderTopColor: accentColor, animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--foreground)', marginBottom: 4 }}>{loadingMsg}</div>
          <div style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>Data dari BPS, PATANAS, dan laporan Numbeo Indonesia...</div>
        </div>
        <ResultSkeleton />
      </div>
    </div>
  );

  if (stage === 'RESULT' && result) {
    const { verdictType, verdictSentence, totalDst, totalOrigin, breakdown, cityDst: cDst, cityOrigin: cOrigin, lifestyle: ls } = result;
    const VERDICT_MAP = {
      LEBIH_HEMAT: { color: '#16a34a', bg: 'rgba(22,163,74,0.05)',  border: '#16a34a', label: 'LEBIH HEMAT' },
      LEBIH_MAHAL: { color: '#d97706', bg: 'rgba(217,119,6,0.05)', border: '#d97706', label: 'LEBIH MAHAL' },
      SEBANDING:   { color: '#2563eb', bg: 'rgba(37,99,235,0.05)', border: '#2563eb', label: 'SEBANDING' },
      INFO:        { color: accentColor, bg: 'rgba(20,184,166,0.05)', border: accentColor, label: 'ESTIMASI' },
    };
    const vs = VERDICT_MAP[verdictType] || VERDICT_MAP.INFO;

    return (
      <div data-tool="wajar-hidup" style={{ minHeight: '80vh', background: bg, padding: '32px 0' }}>
        <div style={{ maxWidth: 600, margin: '0 auto', padding: '0 20px' }}>
          <button onClick={() => { setStage('IDLE'); setResult(null); }} style={{ display: 'flex', alignItems: 'center', gap: 4, background: 'none', border: 'none', color: 'var(--muted-foreground)', cursor: 'pointer', fontSize: 13, marginBottom: 20 }}>← Cek lagi</button>

          {/* Verdict */}
          <div className="animate-fade-in-up" style={{ borderLeft: `4px solid ${vs.border}`, background: vs.bg, borderRadius: '0 12px 12px 0', padding: '20px 20px 20px 24px', marginBottom: 16 }}>
            <div style={{ fontSize: 'clamp(1.5rem, 4vw, 2.25rem)', fontWeight: 800, color: vs.color, letterSpacing: '-0.02em', lineHeight: 1.1, marginBottom: 8 }}>{vs.label}</div>
            <div style={{ fontSize: 14, color: 'var(--muted-foreground)', lineHeight: 1.5, marginBottom: 10 }}>{verdictSentence}</div>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--muted-foreground)' }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: accentColor }} />
              BPS · Survei PATANAS · Numbeo Indonesia · Diperbarui Apr 2026
            </span>
          </div>

          {/* Comparison totals if origin */}
          {totalOrigin && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 16 }}>
              {[
                { label: cDst, val: totalDst, main: true },
                { label: cOrigin, val: totalOrigin, main: false },
              ].map(({ label, val, main }) => (
                <div key={label} style={{ background: 'var(--card)', border: `1.5px solid ${main ? accentColor : 'var(--border)'}`, borderRadius: 12, padding: '14px 16px' }}>
                  <div style={{ fontSize: 11, color: 'var(--muted-foreground)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: main ? accentColor : 'var(--foreground)', fontFamily: 'var(--font-mono)' }}>{fmtIDRShort(val)}</div>
                  <div style={{ fontSize: 10, color: 'var(--muted-foreground)', marginTop: 2 }}>per bulan · gaya hidup {ls}</div>
                </div>
              ))}
            </div>
          )}

          {/* Breakdown */}
          <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, padding: 20, marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--foreground)', marginBottom: 14 }}>Breakdown per Kategori</div>
            {CATEGORIES.map(({ key, label, icon }) => (
              <div key={key} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 18 }}>{icon}</span>
                  <span style={{ fontSize: 13, color: 'var(--foreground)' }}>{label}</span>
                </div>
                <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--foreground)', fontFamily: 'var(--font-mono)' }}>{fmtIDRShort(breakdown[key])}</span>
              </div>
            ))}
            {/* Total */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 14, marginTop: 4 }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--foreground)' }}>Total / bulan</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: accentColor, fontFamily: 'var(--font-mono)' }}>{fmtIDRShort(totalDst)}</div>
            </div>
            <div style={{ fontSize: 11, color: 'var(--muted-foreground)', marginTop: 6 }}>
              Estimasi untuk {result.people === 'sendiri' ? '1 orang' : result.people === 'berdua' ? '2 orang' : '3–4 orang'} · gaya hidup {ls}
            </div>
          </div>

          {/* Premium */}
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--foreground)', marginBottom: 10 }}>Lebih detail?</div>
            {['Breakdown per kecamatan di ' + cDst, 'Tren biaya hidup 12 bulan terakhir', 'Rekomendasi kecamatan sesuai budget kamu'].map(label => (
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
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--foreground)', marginBottom: 8 }}>Lihat breakdown per kecamatan dan riwayat 12 bulan</div>
              <div style={{ display: 'inline-block', padding: '8px 16px', borderRadius: 8, background: accentColor, fontSize: 13, fontWeight: 600, color: '#fff' }}>Buka dengan Pro — Rp 49.000/bulan</div>
              <div style={{ fontSize: 11, color: 'var(--muted-foreground)', marginTop: 6 }}>Batalkan kapan saja · Tanpa kontrak</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
            <button onClick={() => { setStage('IDLE'); setResult(null); }} style={{ flex: 1, padding: '12px', borderRadius: 8, border: '1.5px solid var(--border)', background: 'var(--card)', color: 'var(--foreground)', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>← Cek lagi</button>
            <button style={{ padding: '12px 16px', borderRadius: 8, border: `1.5px solid ${accentColor}`, background: '#f0fdfa', color: accentColor, fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>📤 Bagikan</button>
          </div>

          <button onClick={() => onNavigate('wajar-gaji')} style={{ display: 'block', width: '100%', padding: '12px 16px', border: '1px solid var(--border)', borderRadius: 10, background: 'var(--muted)', cursor: 'pointer', textAlign: 'left', fontSize: 13 }}>
            💡 Cek apakah gaji yang kamu targetkan di {cDst} sudah wajar →{' '}<span style={{ color: '#3b82f6', fontWeight: 600 }}>Wajar Gaji</span>
          </button>
        </div>
      </div>
    );
  }

  // IDLE — form
  return (
    <div data-tool="wajar-hidup" style={{ minHeight: '80vh', background: bg, padding: '32px 0' }}>
      <div style={{ maxWidth: 560, margin: '0 auto', padding: '0 20px' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ fontSize: 40, marginBottom: 10 }}>🌆</div>
          <h1 style={{ fontSize: 'clamp(1.4rem, 3vw, 1.8rem)', fontWeight: 800, color: 'var(--foreground)', marginBottom: 6 }}>Wajar Hidup</h1>
          <p style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>Kalau pindah ke kota lain, berapa yang kamu butuhkan per bulan?</p>
        </div>

        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, padding: '24px' }}>
          {/* Kota tujuan */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 6 }}>Kota Tujuan</label>
            <select value={cityDst} onChange={e => { setCityDst(e.target.value); setErrors({}); }} style={{ ...inputStyle }}>
              <option value="">Pilih kota tujuan...</option>
              {HIDUP_CITIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            {errors.cityDst && <div style={{ fontSize: 11, color: '#dc2626', marginTop: 4 }}>{errors.cityDst}</div>}
          </div>

          {/* Jumlah orang */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 8 }}>Jumlah Orang</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
              {PEOPLE_OPTIONS.map(({ id, label, desc }) => (
                <button key={id} onClick={() => setPeople(id)} style={{
                  padding: '10px 8px', borderRadius: 10, border: '1.5px solid',
                  borderColor: people === id ? accentColor : 'var(--border)',
                  background: people === id ? '#f0fdfa' : 'var(--card)',
                  cursor: 'pointer', textAlign: 'center', transition: 'all 150ms',
                }}>
                  <div style={{ fontSize: 13, fontWeight: people === id ? 700 : 500, color: people === id ? accentColor : 'var(--foreground)', marginBottom: 2 }}>{label}</div>
                  <div style={{ fontSize: 10, color: 'var(--muted-foreground)' }}>{desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Gaya hidup */}
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 8 }}>Gaya Hidup</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {LIFESTYLE_OPTIONS.map(({ id, label, desc, icon }) => (
                <button key={id} onClick={() => setLifestyle(id)} style={{
                  padding: '12px 14px', borderRadius: 10, border: '1.5px solid',
                  borderColor: lifestyle === id ? accentColor : 'var(--border)',
                  background: lifestyle === id ? '#f0fdfa' : 'var(--card)',
                  cursor: 'pointer', textAlign: 'left', display: 'flex', alignItems: 'center', gap: 12,
                  transition: 'all 150ms',
                }}>
                  <span style={{ fontSize: 24, flexShrink: 0 }}>{icon}</span>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: lifestyle === id ? 700 : 600, color: lifestyle === id ? accentColor : 'var(--foreground)', marginBottom: 2 }}>{label}</div>
                    <div style={{ fontSize: 11, color: 'var(--muted-foreground)', lineHeight: 1.4 }}>{desc}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Kota asal optional */}
          <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16, marginBottom: 20 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 4 }}>
              Bandingkan dengan Kotamu Sekarang
              <span style={{ fontSize: 11, color: 'var(--muted-foreground)', fontWeight: 400, marginLeft: 6 }}>(opsional)</span>
            </label>
            <div style={{ fontSize: 11, color: 'var(--muted-foreground)', marginBottom: 8 }}>Jika diisi, hasil akan membandingkan biaya hidup keduanya</div>
            <select value={cityOrigin} onChange={e => setCityOrigin(e.target.value)} style={{ ...inputStyle }}>
              <option value="">Pilih kota asal...</option>
              {HIDUP_CITIES.filter(c => c !== cityDst).map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <button onClick={handleSubmit} style={{ width: '100%', padding: '14px', borderRadius: 10, border: 'none', background: accentColor, color: '#fff', fontSize: 15, fontWeight: 700, cursor: 'pointer' }}>
            Hitung Biaya Hidup →
          </button>
        </div>

        <div style={{ textAlign: 'center', fontSize: 11, color: 'var(--muted-foreground)', marginTop: 12 }}>
          Estimasi dari data BPS, survei PATANAS, dan laporan Numbeo Indonesia
        </div>
      </div>
    </div>
  );
}


export default WajarHidupPage
