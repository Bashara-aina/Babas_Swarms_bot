// @ts-nocheck
'use client'
import React, { useState, useEffect, useRef } from 'react'
import { SalaryRangeBar, BlurredPremiumSection } from './home'


// Wajar Gaji (polished) + Pricing — exported to window

const GAJI_CITIES = ['Jakarta','Surabaya','Bandung','Bekasi','Tangerang Selatan','Semarang','Medan','Makassar','Denpasar','Yogyakarta','Balikpapan','Malang'];

const JOB_TITLES = [
  'Software Engineer','Backend Engineer','Frontend Engineer','Full Stack Engineer',
  'Data Analyst','Data Scientist','Product Manager','UX Designer','UI Designer',
  'Marketing Manager','Finance Manager','HR Manager','Business Analyst',
  'DevOps Engineer','QA Engineer','Project Manager','Sales Manager',
  'Content Writer','Graphic Designer','Accounting Staff',
];

const BENCHMARK_DATA = {
  'Software Engineer':   { p10: 8000000,  p50: 18000000, p90: 35000000 },
  'Backend Engineer':    { p10: 9000000,  p50: 20000000, p90: 38000000 },
  'Frontend Engineer':   { p10: 8000000,  p50: 17000000, p90: 32000000 },
  'Full Stack Engineer': { p10: 10000000, p50: 22000000, p90: 40000000 },
  'Data Analyst':        { p10: 7000000,  p50: 14000000, p90: 28000000 },
  'Data Scientist':      { p10: 10000000, p50: 20000000, p90: 38000000 },
  'Product Manager':     { p10: 12000000, p50: 24000000, p90: 45000000 },
  'UX Designer':         { p10: 7000000,  p50: 15000000, p90: 28000000 },
  'UI Designer':         { p10: 6000000,  p50: 13000000, p90: 25000000 },
  'Marketing Manager':   { p10: 8000000,  p50: 16000000, p90: 30000000 },
  'Finance Manager':     { p10: 10000000, p50: 20000000, p90: 38000000 },
  'HR Manager':          { p10: 8000000,  p50: 15000000, p90: 27000000 },
  'Business Analyst':    { p10: 8000000,  p50: 16000000, p90: 30000000 },
  'DevOps Engineer':     { p10: 10000000, p50: 22000000, p90: 40000000 },
  'QA Engineer':         { p10: 6000000,  p50: 12000000, p90: 22000000 },
  'Project Manager':     { p10: 9000000,  p50: 18000000, p90: 35000000 },
  'Sales Manager':       { p10: 7000000,  p50: 15000000, p90: 28000000 },
  'Content Writer':      { p10: 4000000,  p50: 8000000,  p90: 16000000 },
  'Graphic Designer':    { p10: 4500000,  p50: 9000000,  p90: 18000000 },
  'Accounting Staff':    { p10: 4000000,  p50: 7500000,  p90: 14000000 },
};

const EXP_MULT = { '0-2': 0.75, '3-5': 1.0, '6-10': 1.3, '10+': 1.6 };

function fmtIDRShort(n) {
  if (!n) return '–';
  if (n >= 1_000_000) return 'Rp\u00a0' + (n / 1_000_000).toFixed(1).replace('.', ',') + ' jt';
  return 'Rp\u00a0' + n.toLocaleString('id-ID');
}

const inputStyle = {
  width: '100%', boxSizing: 'border-box', height: 52, padding: '0 14px',
  border: '1.5px solid var(--border)', borderRadius: 10,
  background: 'var(--card)', color: 'var(--foreground)',
  fontSize: 15, fontFamily: 'inherit', outline: 'none', transition: 'border-color 150ms',
};

function WajarGajiPage({ onNavigate }) {
  const [stage, setStage] = useState('IDLE');
  const [jobTitle, setJobTitle] = useState('');
  const [city, setCity] = useState('Jakarta');
  const [exp, setExp] = useState('3-5');
  const [userSalary, setUserSalary] = useState('');
  const [autocomplete, setAutocomplete] = useState([]);
  const [showAC, setShowAC] = useState(false);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [result, setResult] = useState(null);
  const [errors, setErrors] = useState({});
  const [showRefine, setShowRefine] = useState(false);
  const [edu, setEdu] = useState('');
  const [industry, setIndustry] = useState('');
  const acRef = useRef(null);

  useEffect(() => {
    if (jobTitle.length < 2) { setAutocomplete([]); setShowAC(false); return; }
    const matches = JOB_TITLES.filter(t => t.toLowerCase().includes(jobTitle.toLowerCase())).slice(0, 6);
    setAutocomplete(matches);
    setShowAC(matches.length > 0);
  }, [jobTitle]);

  useEffect(() => {
    const h = e => { if (acRef.current && !acRef.current.contains(e.target)) setShowAC(false); };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);

  const handleSearch = () => {
    const errs = {};
    if (!jobTitle) errs.jobTitle = 'Pilih judul pekerjaan';
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    setStage('SEARCHING');

    const msgs = [
      `Mencari data untuk ${jobTitle} di ${city}...`,
      'Memuat 12.000+ data karyawan...',
      `Menghitung rentang gaji pengalaman ${exp} tahun...`,
    ];
    let i = 0;
    setLoadingMsg(msgs[0]);
    const iv = setInterval(() => { i++; if (i < msgs.length) setLoadingMsg(msgs[i]); }, 700);

    setTimeout(() => {
      clearInterval(iv);
      const base = BENCHMARK_DATA[jobTitle] || { p10: 6000000, p50: 12000000, p90: 24000000 };
      const mult = EXP_MULT[exp] || 1;
      const p10 = Math.round(base.p10 * mult);
      const p50 = Math.round(base.p50 * mult);
      const p90 = Math.round(base.p90 * mult);
      const userVal = userSalary ? parseInt(userSalary.replace(/\D/g,''), 10) : null;

      let verdictType = 'WAJAR';
      let verdictSentence = `Rentang gaji untuk ${jobTitle} di ${city} dengan pengalaman ${exp} tahun.`;
      if (userVal) {
        const pct = Math.round((userVal - p50) / p50 * 100);
        if (pct < -15) {
          verdictType = 'DI_BAWAH';
          verdictSentence = `Gaji kamu ${Math.abs(pct)}% di bawah median untuk posisi ini di ${city}. Ada ruang untuk negosiasi.`;
        } else if (pct > 15) {
          verdictType = 'DI_ATAS';
          verdictSentence = `Gaji kamu ${pct}% di atas median. Kamu berada di posisi yang sangat kompetitif.`;
        } else {
          verdictType = 'WAJAR';
          verdictSentence = `Gaji kamu berada di kisaran wajar untuk ${jobTitle} di ${city}. Sebanding dengan median pasar.`;
        }
      }

      setResult({ p10, p50, p90, userVal, verdictType, verdictSentence, sampleCount: 312 + Math.floor(Math.random()*80), jobTitle, city, exp });
      setStage('RESULT');
    }, 2400);
  };

  if (stage === 'SEARCHING') return (
    <div data-tool="wajar-gaji" style={{ minHeight: '80vh', background: '#eff6ff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center', maxWidth: 320, padding: '0 24px' }}>
        <div style={{ width: 56, height: 56, borderRadius: '50%', border: '4px solid #bfdbfe', borderTopColor: '#3b82f6', animation: 'spin 1s linear infinite', margin: '0 auto 20px' }} />
        <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--foreground)', marginBottom: 6 }}>{loadingMsg}</div>
        <div style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>Memproses 12.000+ data gaji…</div>
      </div>
    </div>
  );

  if (stage === 'RESULT' && result) {
    const { p10, p50, p90, userVal, verdictType, verdictSentence, sampleCount } = result;
    const VERDICT_MAP = {
      WAJAR:    { color: '#16a34a', bg: 'rgba(22,163,74,0.05)',  border: '#16a34a', label: 'WAJAR' },
      DI_ATAS:  { color: '#16a34a', bg: 'rgba(22,163,74,0.05)',  border: '#16a34a', label: 'DI ATAS PASARAN' },
      DI_BAWAH: { color: '#dc2626', bg: 'rgba(220,38,38,0.05)', border: '#dc2626', label: 'DI BAWAH PASARAN' },
    };
    const vs = VERDICT_MAP[verdictType] || VERDICT_MAP.WAJAR;
    const crossTool = verdictType === 'DI_BAWAH'
      ? { msg: 'Cek juga apakah slip gajimu dipotong benar', to: 'wajar-slip', label: 'Wajar Slip' }
      : { msg: 'Hitung biaya hidup di kotamu', to: 'wajar-hidup', label: 'Wajar Hidup' };

    return (
      <div data-tool="wajar-gaji" style={{ minHeight: '80vh', background: '#eff6ff', padding: '32px 0' }}>
        <div style={{ maxWidth: 600, margin: '0 auto', padding: '0 20px' }}>
          <button onClick={() => { setStage('IDLE'); setResult(null); setShowRefine(false); }} style={{ display: 'flex', alignItems: 'center', gap: 4, background: 'none', border: 'none', color: 'var(--muted-foreground)', cursor: 'pointer', fontSize: 13, marginBottom: 20 }}>← Cek lagi</button>

          {/* VERDICT — dominant, sentence prominent */}
          <div className="animate-fade-in-up" style={{ borderLeft: `4px solid ${vs.border}`, background: vs.bg, borderRadius: '0 12px 12px 0', padding: '20px 20px 20px 24px', marginBottom: 16 }}>
            <div style={{ fontSize: 'clamp(1.5rem, 4vw, 2.25rem)', fontWeight: 800, color: vs.color, letterSpacing: '-0.02em', lineHeight: 1.1, marginBottom: 10 }}>{vs.label}</div>
            <div style={{ fontSize: 15, color: 'var(--foreground)', lineHeight: 1.6, marginBottom: 12, fontWeight: 500 }}>{verdictSentence}</div>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--muted-foreground)' }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: sampleCount >= 100 ? '#10b981' : '#f59e0b' }} />
              {sampleCount >= 100 ? 'Tinggi' : 'Sedang'} · BPS + {sampleCount} laporan · Diperbarui Apr 2026
            </span>
          </div>

          {/* Range bar card */}
          <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, padding: '20px', marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--foreground)', marginBottom: 14 }}>
              Rentang Gaji — {result.jobTitle} di {result.city}
            </div>
            <SalaryRangeBar p10={p10} p50={p50} p90={p90} userSalary={userVal} />
            <div style={{ fontSize: 11, color: 'var(--muted-foreground)', marginTop: 8, fontFamily: 'var(--font-mono)' }}>
              Pengalaman {result.exp} tahun · Data UMK {result.city} Q1 2026 — Kemnaker
            </div>
          </div>

          {/* Refine result row */}
          {!showRefine ? (
            <button onClick={() => setShowRefine(true)} style={{
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              width: '100%', padding: '12px 16px', borderRadius: 10,
              border: '1px dashed var(--border)', background: 'var(--muted)',
              cursor: 'pointer', fontSize: 13, color: 'var(--muted-foreground)',
              marginBottom: 16,
            }}>
              <span>Perhalus hasil: tambahkan pendidikan, industri, ukuran perusahaan →</span>
              <span style={{ color: '#3b82f6', fontWeight: 600, marginLeft: 8 }}>▾</span>
            </button>
          ) : (
            <div style={{ background: 'var(--card)', border: '1.5px solid #bfdbfe', borderRadius: 12, padding: '16px', marginBottom: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#1d4ed8', marginBottom: 12 }}>Perhalus Hasil</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--foreground)', marginBottom: 5 }}>Pendidikan</label>
                  <select value={edu} onChange={e => setEdu(e.target.value)} style={{ ...inputStyle, height: 42, fontSize: 13 }}>
                    <option value="">Semua</option>
                    <option>SMA/SMK</option><option>D3</option><option>S1</option><option>S2/S3</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: 'var(--foreground)', marginBottom: 5 }}>Industri</label>
                  <select value={industry} onChange={e => setIndustry(e.target.value)} style={{ ...inputStyle, height: 42, fontSize: 13 }}>
                    <option value="">Semua</option>
                    <option>Teknologi</option><option>Keuangan</option><option>E-commerce</option>
                    <option>FMCG</option><option>Healthcare</option><option>Konsultan</option>
                  </select>
                </div>
              </div>
              <button onClick={() => setShowRefine(false)} style={{ fontSize: 12, color: 'var(--muted-foreground)', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>
                Tutup filter
              </button>
            </div>
          )}

          {/* Premium blurred */}
          <BlurredPremiumSection onUpgrade={() => onNavigate('pricing')} />

          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 14 }}>
            <button onClick={() => { setStage('IDLE'); setResult(null); setShowRefine(false); }} style={{ flex: 1, padding: '12px', borderRadius: 8, border: '1.5px solid var(--border)', background: 'var(--card)', color: 'var(--foreground)', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>← Cek lagi</button>
            <button style={{ padding: '12px 16px', borderRadius: 8, border: '1.5px solid #3b82f6', background: '#eff6ff', color: '#1d4ed8', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>📤 Bagikan</button>
          </div>

          <button onClick={() => onNavigate(crossTool.to)} style={{ display: 'block', width: '100%', padding: '12px 16px', border: '1px solid var(--border)', borderRadius: 10, background: 'var(--muted)', cursor: 'pointer', textAlign: 'left', fontSize: 13 }}>
            💡 {crossTool.msg} →{' '}<span style={{ color: '#10b981', fontWeight: 600 }}>{crossTool.label}</span>
          </button>
        </div>
      </div>
    );
  }

  // IDLE — form
  return (
    <div data-tool="wajar-gaji" style={{ minHeight: '80vh', background: '#eff6ff', padding: '32px 0' }}>
      <div style={{ maxWidth: 560, margin: '0 auto', padding: '0 20px' }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>💰</div>
          <h1 style={{ fontSize: 'clamp(1.4rem, 3vw, 1.8rem)', fontWeight: 800, color: 'var(--foreground)', marginBottom: 6 }}>Cek Wajar Gaji</h1>
          <p style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>Benchmark gaji dengan 12.000+ data karyawan Indonesia</p>
        </div>

        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, padding: '24px' }}>
          {/* Autocomplete job title */}
          <div style={{ marginBottom: 16 }} ref={acRef}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 6 }}>Judul Pekerjaan</label>
            <div style={{ position: 'relative' }}>
              <input value={jobTitle} onChange={e => { setJobTitle(e.target.value); setErrors({}); }}
                onFocus={() => jobTitle.length >= 2 && setShowAC(true)}
                placeholder="cth. Software Engineer" style={inputStyle} />
              {showAC && autocomplete.length > 0 && (
                <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 50, background: 'var(--card)', border: '1.5px solid var(--border)', borderRadius: 10, boxShadow: '0 8px 24px rgba(0,0,0,0.1)', marginTop: 4, overflow: 'hidden' }}>
                  {autocomplete.map(t => (
                    <button key={t} onClick={() => { setJobTitle(t); setShowAC(false); }} style={{ display: 'block', width: '100%', textAlign: 'left', padding: '11px 14px', border: 'none', background: 'transparent', fontSize: 14, color: 'var(--foreground)', cursor: 'pointer', borderBottom: '1px solid var(--border)' }}
                      onMouseEnter={e => e.currentTarget.style.background = 'var(--muted)'}
                      onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                    >{t}</button>
                  ))}
                </div>
              )}
            </div>
            {errors.jobTitle && <div style={{ fontSize: 11, color: '#dc2626', marginTop: 4 }}>{errors.jobTitle}</div>}
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 6 }}>Kota</label>
            <select value={city} onChange={e => setCity(e.target.value)} style={inputStyle}>
              {GAJI_CITIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)' }}>Pengalaman Kerja</label>
              <span style={{ fontSize: 13, fontWeight: 700, color: '#3b82f6' }}>{exp} tahun</span>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              {['0-2','3-5','6-10','10+'].map(v => (
                <button key={v} onClick={() => setExp(v)} style={{ flex: 1, padding: '10px 6px', borderRadius: 8, border: '1.5px solid', borderColor: exp === v ? '#3b82f6' : 'var(--border)', background: exp === v ? '#eff6ff' : 'var(--card)', color: exp === v ? '#1d4ed8' : 'var(--muted-foreground)', fontSize: 12, fontWeight: exp === v ? 700 : 500, cursor: 'pointer', transition: 'all 150ms' }}>
                  {v}
                </button>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)' }}>Gaji Kamu</label>
              <span style={{ fontSize: 11, color: 'var(--muted-foreground)' }}>(opsional)</span>
            </div>
            <input value={userSalary} onChange={e => { const r = e.target.value.replace(/\D/g,''); setUserSalary(r ? parseInt(r,10).toLocaleString('id-ID') : ''); }} placeholder="cth. 14.000.000" style={inputStyle} />
            <div style={{ fontSize: 11, color: 'var(--muted-foreground)', marginTop: 4 }}>Kosongkan jika hanya ingin lihat benchmark</div>
          </div>

          <button onClick={handleSearch} style={{ width: '100%', padding: '14px', borderRadius: 10, border: 'none', background: '#3b82f6', color: '#fff', fontSize: 15, fontWeight: 700, cursor: 'pointer' }}>
            Cek Wajar Gaji →
          </button>
        </div>

        <div style={{ marginTop: 14, padding: '14px', borderRadius: 10, background: '#eff6ff', border: '1px solid #bfdbfe', display: 'flex', gap: 10, alignItems: 'flex-start' }}>
          <span style={{ fontSize: 16 }}>ℹ️</span>
          <div style={{ fontSize: 12, color: '#1e40af' }}>
            <strong>Data dari mana?</strong> 200+ judul pekerjaan, 50+ kota. Digabung dari BPS dan laporan anonim karyawan.
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Pricing Page ─────────────────────────────────────────────────────────────

function PricingPage({ onNavigate }) {
  const [annual, setAnnual] = useState(true);

  const proMonthly = 49000;
  const proAnnual = Math.round(proMonthly * 12 * 0.833);
  const saving = proMonthly * 12 - proAnnual;

  function fmtP(n) { return 'Rp\u00a0' + n.toLocaleString('id-ID'); }

  const tiers = [
    {
      name: 'Gratis', price: 'Rp 0', period: '', badge: null,
      cta: 'Mulai Sekarang', ctaAction: () => onNavigate('wajar-slip'),
      ctaStyle: { background: 'var(--muted)', color: 'var(--foreground)', border: '1.5px solid var(--border)' },
      features: ['Akses semua 5 alat','Audit slip gaji verdict instan','Benchmark gaji (data median)','3 audit slip per bulan','Hasil bisa dibagikan via WhatsApp'],
      notIncluded: ['Tren gaji 12 bulan ke belakang','Data P25–P75 per kota','Template negosiasi gaji','Riwayat hasil tersimpan'],
    },
    {
      name: 'Pro', price: annual ? fmtP(Math.round(proAnnual/12)) : fmtP(proMonthly), period: '/bulan', badge: 'Paling Populer',
      cta: 'Mulai Pro', ctaAction: () => {},
      ctaStyle: { background: '#10b981', color: '#fff', border: 'none' },
      annualNote: annual ? `Tagih tahunan · Hemat ${fmtP(saving)}/tahun` : null,
      features: ['Semua fitur Gratis','Audit slip tak terbatas','Tren gaji 12 bulan ke belakang','Data P10, P25, P75, P90 per kota','Template negosiasi untuk posisi kamu','Riwayat hasil tersimpan (12 bulan)','Perbandingan biaya hidup detail','Export hasil ke PDF'],
      notIncluded: [],
    },
    {
      name: 'Tim', price: 'Hubungi Kami', period: '', badge: null,
      cta: 'Hubungi Sales', ctaAction: () => {},
      ctaStyle: { background: 'var(--foreground)', color: 'var(--background)', border: 'none' },
      features: ['Semua fitur Pro','Akses tim (5–50 pengguna)','Dasbor HR untuk analisis tim','Benchmark gaji untuk rekrutmen','Laporan internal per departemen','SSO & integrasi HRIS','SLA support prioritas'],
      notIncluded: [],
    },
  ];

  return (
    <div style={{ minHeight: '80vh', background: 'var(--background)', padding: '48px 24px' }}>
      <div style={{ maxWidth: 900, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <h1 style={{ fontSize: 'clamp(1.8rem, 4vw, 2.5rem)', fontWeight: 800, color: 'var(--foreground)', letterSpacing: '-0.02em', marginBottom: 10 }}>Pilih Plan yang Sesuai</h1>
          <p style={{ fontSize: 15, color: 'var(--muted-foreground)', marginBottom: 24 }}>Mulai gratis, upgrade saat butuh lebih dalam.</p>
          <div style={{ display: 'inline-flex', alignItems: 'center', background: 'var(--muted)', borderRadius: 99, padding: '4px' }}>
            {[{ label: 'Tahunan', val: true }, { label: 'Bulanan', val: false }].map(({ label, val }) => (
              <button key={String(val)} onClick={() => setAnnual(val)} style={{ padding: '8px 20px', borderRadius: 99, border: 'none', background: annual === val ? 'var(--card)' : 'transparent', color: annual === val ? 'var(--foreground)' : 'var(--muted-foreground)', fontWeight: annual === val ? 700 : 500, fontSize: 14, cursor: 'pointer', boxShadow: annual === val ? '0 1px 6px rgba(0,0,0,0.08)' : 'none', transition: 'all 200ms', fontFamily: 'inherit' }}>
                {label}
                {val && <span style={{ marginLeft: 6, fontSize: 10, background: '#10b981', color: '#fff', borderRadius: 99, padding: '2px 6px', fontWeight: 700 }}>2 bulan gratis</span>}
              </button>
            ))}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 16, alignItems: 'start' }}>
          {tiers.map(({ name, price, period, badge, cta, ctaAction, ctaStyle, features, notIncluded, annualNote }) => (
            <div key={name} style={{ border: `2px solid ${name === 'Pro' ? '#10b981' : 'var(--border)'}`, borderRadius: 16, padding: '24px', background: name === 'Pro' ? 'linear-gradient(135deg, #f0fdf4, #ecfdf5)' : 'var(--card)', position: 'relative' }}>
              {badge && <div style={{ position: 'absolute', top: -12, left: '50%', transform: 'translateX(-50%)', background: '#10b981', color: '#fff', fontSize: 11, fontWeight: 700, padding: '4px 14px', borderRadius: 99 }}>{badge}</div>}
              <div style={{ marginBottom: 20 }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--muted-foreground)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>{name}</div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: 2 }}>
                  <span style={{ fontSize: name === 'Tim' ? 18 : 26, fontWeight: 800, color: 'var(--foreground)', fontFamily: name === 'Tim' ? 'inherit' : 'var(--font-mono)', letterSpacing: '-0.02em' }}>{price}</span>
                  <span style={{ fontSize: 13, color: 'var(--muted-foreground)', fontWeight: 500 }}>{period}</span>
                </div>
                {annualNote && <div style={{ fontSize: 11, color: '#059669', marginTop: 4, fontWeight: 600 }}>{annualNote}</div>}
              </div>
              <button onClick={ctaAction} style={{ width: '100%', padding: '12px', borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: 'pointer', marginBottom: 20, fontFamily: 'inherit', ...ctaStyle }}>{cta}</button>
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16 }}>
                {features.map(f => (
                  <div key={f} style={{ display: 'flex', gap: 8, marginBottom: 8, fontSize: 13, color: 'var(--foreground)' }}>
                    <span style={{ color: '#10b981', flexShrink: 0 }}>✓</span><span>{f}</span>
                  </div>
                ))}
                {notIncluded.map(f => (
                  <div key={f} style={{ display: 'flex', gap: 8, marginBottom: 8, fontSize: 13, color: 'var(--muted-foreground)' }}>
                    <span style={{ flexShrink: 0 }}>–</span><span>{f}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        <div style={{ textAlign: 'center', marginTop: 32, fontSize: 13, color: 'var(--muted-foreground)' }}>
          Sudah 2.400+ pengguna Pro · Batalkan kapan saja · Tanpa kontrak
        </div>
      </div>
    </div>
  );
}


export { WajarGajiPage, PricingPage }
