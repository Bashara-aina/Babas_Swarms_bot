// @ts-nocheck
'use client'
import React, { useState, useEffect, useRef } from 'react'
import { VerdictCard, BlurredPremiumSection, fmtIDR } from './home'


// Wajar Slip Page — exported to window
const MONTHS = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'];
const PTKP_OPTIONS = ['TK/0','TK/1','TK/2','TK/3','K/0','K/1','K/2','K/3','K/I/0','K/I/1','K/I/2','K/I/3'];
const CITIES = ['Jakarta','Surabaya','Bandung','Bekasi','Tangerang Selatan','Semarang','Medan','Makassar','Denpasar','Yogyakarta','Balikpapan','Malang','Pontianak'];

function parseIDR(s) { return parseInt((s || '').replace(/\D/g,'') || '0', 10); }
function fmtInput(n) { return n ? n.toLocaleString('id-ID') : ''; }
function idrInput(val, onChange) {
  return {
    value: val,
    onChange: e => {
      const raw = e.target.value.replace(/\D/g,'');
      onChange(raw ? parseInt(raw,10).toLocaleString('id-ID') : '');
    }
  };
}

// Step indicator
function Steps({ current }) {
  const steps = ['Upload', 'Konfirmasi', 'Hasil'];
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, marginBottom: 24 }}>
      {steps.map((s, i) => (
        <React.Fragment key={s}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: 60 }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%', border: '2px solid',
              borderColor: i <= current ? '#10b981' : 'var(--border)',
              background: i < current ? '#10b981' : i === current ? '#ecfdf5' : 'var(--card)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 11, fontWeight: 700,
              color: i < current ? '#fff' : i === current ? '#059669' : 'var(--muted-foreground)',
              transition: 'all 300ms',
            }}>
              {i < current ? '✓' : i + 1}
            </div>
            <div style={{ fontSize: 10, marginTop: 4, color: i <= current ? '#059669' : 'var(--muted-foreground)', fontWeight: i === current ? 700 : 400 }}>{s}</div>
          </div>
          {i < steps.length - 1 && (
            <div style={{ flex: 1, height: 2, background: i < current ? '#10b981' : 'var(--border)', margin: '0 2px 14px', transition: 'background 300ms' }} />
          )}
        </React.Fragment>
      ))}
    </div>
  );
}

// Field with label
function Field({ label, hint, error, children, optional }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
        <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)' }}>
          {label}
          {optional && <span style={{ fontSize: 11, color: 'var(--muted-foreground)', fontWeight: 400, marginLeft: 6 }}>(opsional)</span>}
        </label>
        {hint && <span style={{ fontSize: 11, color: 'var(--muted-foreground)' }}>{hint}</span>}
      </div>
      {children}
      {error && <div style={{ fontSize: 11, color: '#dc2626', marginTop: 4 }}>{error}</div>}
    </div>
  );
}

const inputStyle = {
  width: '100%', boxSizing: 'border-box',
  height: 48, padding: '0 14px',
  border: '1.5px solid var(--border)', borderRadius: 8,
  background: 'var(--card)', color: 'var(--foreground)',
  fontSize: 15, fontFamily: 'inherit',
  outline: 'none', transition: 'border-color 150ms',
};

function Inp({ style, ...props }) {
  const [focused, setFocused] = useState(false);
  return (
    <input
      {...props}
      style={{ ...inputStyle, ...(focused ? { borderColor: '#10b981' } : {}), ...style }}
      onFocus={() => setFocused(true)}
      onBlur={() => setFocused(false)}
    />
  );
}

function Sel({ value, onChange, options, style }) {
  const [focused, setFocused] = useState(false);
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      style={{ ...inputStyle, ...(focused ? { borderColor: '#10b981' } : {}), ...style }}
      onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
    >
      {options.map(o => typeof o === 'string'
        ? <option key={o} value={o}>{o}</option>
        : <option key={o.value} value={o.value}>{o.label}</option>
      )}
    </select>
  );
}

// Upload zone — full-screen feel on mobile
function UploadZone({ onContinue }) {
  const [dragging, setDragging] = useState(false);
  const [uploaded, setUploaded] = useState(false);

  return (
    <div>
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={e => { e.preventDefault(); setDragging(false); setUploaded(true); }}
        onClick={() => setUploaded(true)}
        style={{
          border: `2px dashed ${dragging ? '#10b981' : uploaded ? '#10b981' : '#fbbf24'}`,
          borderRadius: 20,
          padding: 'clamp(40px, 10vw, 72px) 24px',
          textAlign: 'center',
          background: dragging ? 'rgba(16,185,129,0.04)' : uploaded ? 'rgba(16,185,129,0.04)' : '#fffbeb',
          transition: 'all 200ms', cursor: 'pointer',
          marginBottom: 12,
          minHeight: 280,
          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        }}
      >
        {uploaded ? (
          <>
            <div style={{ fontSize: 52, marginBottom: 14 }}>✅</div>
            <div style={{ fontSize: 17, fontWeight: 800, color: '#059669', marginBottom: 4 }}>slip_gaji_april.pdf</div>
            <div style={{ fontSize: 13, color: 'var(--muted-foreground)', marginBottom: 20 }}>OCR selesai — 12 field terdeteksi</div>
            <button onClick={e => { e.stopPropagation(); onContinue(); }} style={{ padding: '13px 28px', borderRadius: 10, border: 'none', background: '#10b981', color: '#fff', fontSize: 15, fontWeight: 700, cursor: 'pointer' }}>
              Konfirmasi & Audit →
            </button>
          </>
        ) : (
          <>
            <div style={{ fontSize: 56, marginBottom: 14, filter: 'drop-shadow(0 4px 8px rgba(245,158,11,0.2))' }}>📋</div>
            <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--foreground)', marginBottom: 6 }}>Upload slip gaji kamu</div>
            <div style={{ fontSize: 13, color: 'var(--muted-foreground)', marginBottom: 24, maxWidth: 260, lineHeight: 1.6 }}>
              Foto atau PDF. Drag &amp; drop ke sini, atau tap tombol di bawah.
            </div>
            <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
              <button style={{ padding: '12px 22px', borderRadius: 10, border: 'none', background: '#f59e0b', color: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}>
                📸 Ambil Foto
              </button>
              <button style={{ padding: '12px 22px', borderRadius: 10, border: '1.5px solid var(--border)', background: 'var(--card)', color: 'var(--foreground)', fontSize: 14, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}>
                📁 Pilih File
              </button>
            </div>
          </>
        )}
      </div>

      {/* Security note */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', borderRadius: 8, background: 'var(--muted)', fontSize: 12, color: 'var(--muted-foreground)', marginBottom: 16 }}>
        <span>🔒</span>
        <span>Aman. Enkripsi end-to-end. Tidak disimpan setelah audit.</span>
      </div>

      <p style={{ textAlign: 'center', fontSize: 12, color: 'var(--muted-foreground)' }}>
        Atau{' '}
        <button onClick={onContinue} style={{ background: 'none', border: 'none', color: '#d97706', fontSize: 12, cursor: 'pointer', textDecoration: 'underline', fontWeight: 600 }}>
          isi form manual
        </button>
        {' '}— untuk slip fisik atau input langsung
      </p>
    </div>
  );
}

// Violation item
function ViolationItem({ code, title, desc, diff, correct }) {
  const isCritical = ['V03','V06'].includes(code);
  return (
    <div style={{
      border: `1.5px solid ${isCritical ? '#fca5a5' : '#fde68a'}`,
      borderLeft: `4px solid ${isCritical ? '#dc2626' : '#f59e0b'}`,
      borderRadius: '0 10px 10px 0',
      padding: '14px 16px',
      background: isCritical ? 'rgba(220,38,38,0.03)' : 'rgba(245,158,11,0.03)',
      marginBottom: 10,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--foreground)', marginBottom: 2 }}>
            {title}
          </div>
          <div style={{ fontSize: 12, color: 'var(--muted-foreground)', lineHeight: 1.5 }}>{desc}</div>
        </div>
        {diff && (
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#dc2626', fontFamily: 'var(--font-mono)' }}>
              −{fmtIDR ? fmtIDR(diff) : `Rp ${diff.toLocaleString('id-ID')}`}
            </div>
            <div style={{ fontSize: 10, color: 'var(--muted-foreground)' }}>selisih/bulan</div>
          </div>
        )}
      </div>
    </div>
  );
}

// Main Wajar Slip Page
function WajarSlipPage({ onNavigate }) {
  const [stage, setStage] = useState('IDLE'); // IDLE | FORM | CALCULATING | VERDICT
  const [loadingMsg, setLoadingMsg] = useState('');

  // Form state
  const [gross, setGross] = useState('');
  const [ptkp, setPtkp] = useState('TK/0');
  const [city, setCity] = useState('Jakarta');
  const [month, setMonth] = useState('4');
  const [year] = useState('2026');
  const [hasNPWP, setHasNPWP] = useState(true);
  const [pph21, setPph21] = useState('');
  const [jht, setJht] = useState('');
  const [jp, setJp] = useState('');
  const [kes, setKes] = useState('');
  const [takeHome, setTakeHome] = useState('');
  const [errors, setErrors] = useState({});
  const [verdictData, setVerdictData] = useState(null);

  const loadingMsgs = [
    'Membaca dan menganalisis slip gajimu...',
    'Mengecek tarif PPh21 TER (PMK 168/2023)...',
    'Memverifikasi potongan BPJS Ketenagakerjaan...',
    'Membandingkan dengan UMK ' + city + ' Q1 2026...',
    'Menyusun laporan pelanggaran...',
  ];

  const runCalculation = () => {
    const g = parseIDR(gross);
    const errs = {};
    if (!g || g < 500000) errs.gross = 'Masukkan gaji bruto yang valid';
    if (!city) errs.city = 'Pilih kota';
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    setStage('CALCULATING');

    // Simulate calculation with loading msgs
    let i = 0;
    setLoadingMsg(loadingMsgs[0]);
    const interval = setInterval(() => {
      i++;
      if (i < loadingMsgs.length) setLoadingMsg(loadingMsgs[i]);
    }, 600);

    setTimeout(() => {
      clearInterval(interval);
      // Simulate verdict — calculate expected PPh21 ~1.5% of gross
      const reportedPph = parseIDR(pph21);
      const correctPph = Math.round(g * 0.015);
      const reportedJhtV = parseIDR(jht);
      const correctJht = Math.round(g * 0.02);
      const reportedKes = parseIDR(kes);
      const correctKes = Math.round(Math.min(g, 12000000) * 0.01);

      const violations = [];
      if (reportedJhtV > 0 && Math.abs(reportedJhtV - correctJht) > correctJht * 0.05) {
        violations.push({
          code: 'V01', title: 'JHT Karyawan Tidak Sesuai',
          desc: `Seharusnya 2% dari gaji bruto = Rp ${correctJht.toLocaleString('id-ID')}`,
          diff: Math.abs(reportedJhtV - correctJht),
        });
      }
      if (reportedPph > 0 && Math.abs(reportedPph - correctPph) > correctPph * 0.1) {
        violations.push({
          code: 'V03', title: 'PPh21 Kurang Dipotong',
          desc: `Berdasarkan TER PMK 168/2023, seharusnya Rp ${correctPph.toLocaleString('id-ID')}`,
          diff: Math.abs(reportedPph - correctPph),
        });
      }
      if (g < 5200000 && city === 'Jakarta') {
        violations.push({
          code: 'V06', title: 'Gaji Di Bawah UMK Jakarta',
          desc: 'UMK DKI Jakarta Q1 2026 = Rp 5.200.000. Gaji bruto kamu di bawah batas minimum.',
          diff: null,
        });
      }

      setVerdictData({
        verdict: violations.length > 0 ? 'ADA_PELANGGARAN' : 'SESUAI',
        violations,
        grossSalary: g,
        city,
        month: MONTHS[parseInt(month) - 1],
        calculations: { correctPph21: correctPph, correctJht, correctKes },
        cityUMK: 5200000,
      });
      setStage('VERDICT');
    }, 3200);
  };

  if (stage === 'IDLE') return (
    <div data-tool="wajar-slip" style={{ minHeight: '80vh', background: '#fffbeb', padding: '32px 0' }}>
      <div style={{ maxWidth: 560, margin: '0 auto', padding: '0 20px' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <h1 style={{ fontSize: 'clamp(1.4rem, 3vw, 1.8rem)', fontWeight: 800, color: 'var(--foreground)', marginBottom: 6 }}>
            Cek Slip Gaji — Gratis
          </h1>
          <p style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>
            Pastikan PPh21 dan BPJS sudah dipotong dengan benar. Hanya butuh 30 detik.
          </p>
        </div>
        <Steps current={0} />
        <UploadZone onContinue={() => setStage('FORM')} />
      </div>
    </div>
  );

  if (stage === 'CALCULATING') return (
    <div data-tool="wajar-slip" style={{ minHeight: '80vh', background: '#fffbeb', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ textAlign: 'center', maxWidth: 320, padding: '0 24px' }}>
        <div style={{
          width: 56, height: 56, borderRadius: '50%',
          border: '4px solid #fde68a', borderTopColor: '#f59e0b',
          animation: 'spin 1s linear infinite',
          margin: '0 auto 20px',
        }} />
        <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--foreground)', marginBottom: 6 }}>{loadingMsg}</div>
        <div style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>Biasanya selesai dalam 30 detik</div>
      </div>
    </div>
  );

  if (stage === 'VERDICT' && verdictData) {
    const { verdict, violations, grossSalary, city: c, month: m, calculations } = verdictData;
    const isClean = verdict === 'SESUAI';
    return (
      <div data-tool="wajar-slip" style={{ minHeight: '80vh', background: '#fffbeb', padding: '32px 0' }}>
        <div style={{ maxWidth: 560, margin: '0 auto', padding: '0 20px' }}>
          <Steps current={2} />

          {/* Verdict card */}
          <div className="animate-fade-in-up">
            <VerdictCard
              type={verdict}
              sentence={isClean
                ? `Tidak ada pelanggaran ditemukan. Gaji bruto Rp ${grossSalary.toLocaleString('id-ID')}/bulan, ${m} 2026.`
                : `Ditemukan ${violations.length} pelanggaran pada slip gaji kamu. Segera tindaklanjuti.`
              }
              confidenceProps={{ level: 'Tinggi', source: 'PMK 168/2023 + BPJS', updated: 'Apr 2026' }}
            />
          </div>

          {/* UMK badge */}
          <div style={{
            padding: '10px 14px', background: 'var(--muted)', borderRadius: 8,
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            marginBottom: 16, fontSize: 13,
          }}>
            <span style={{ color: 'var(--muted-foreground)' }}>UMK {c} 2026</span>
            <span style={{ fontWeight: 700, color: 'var(--foreground)', fontFamily: 'var(--font-mono)' }}>Rp 5.200.000</span>
          </div>

          {/* Violations */}
          {violations.length > 0 && (
            <div style={{ marginBottom: 20 }}>
              {violations.map(v => <ViolationItem key={v.code} {...v} />)}
            </div>
          )}

          {/* Calculation table (free) */}
          <div style={{
            background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 12,
            padding: '16px', marginBottom: 20,
          }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--foreground)', marginBottom: 12 }}>Rincian Kalkulasi</div>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  <th style={{ textAlign: 'left', padding: '6px 0', color: 'var(--muted-foreground)', fontWeight: 500 }}>Komponen</th>
                  <th style={{ textAlign: 'right', padding: '6px 4px', color: 'var(--muted-foreground)', fontWeight: 500 }}>Di Slip</th>
                  <th style={{ textAlign: 'right', padding: '6px 4px', color: 'var(--muted-foreground)', fontWeight: 500 }}>Seharusnya</th>
                  <th style={{ textAlign: 'right', padding: '6px 0', color: 'var(--muted-foreground)', fontWeight: 500 }}>Selisih</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { label: 'PPh21', slip: parseIDR(pph21) || calculations.correctPph21, correct: calculations.correctPph21 },
                  { label: 'JHT (2%)', slip: parseIDR(jht) || calculations.correctJht, correct: calculations.correctJht },
                  { label: 'JP (1%)', slip: parseIDR(jp) || Math.round(grossSalary * 0.01), correct: Math.round(grossSalary * 0.01) },
                  { label: 'BPJS Kes (1%)', slip: parseIDR(kes) || calculations.correctKes, correct: calculations.correctKes },
                ].map(({ label, slip, correct }) => {
                  const diff = correct - slip;
                  return (
                    <tr key={label} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '8px 0', fontWeight: 600 }}>{label}</td>
                      <td style={{ padding: '8px 4px', textAlign: 'right', color: 'var(--muted-foreground)', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                        Rp {slip.toLocaleString('id-ID')}
                      </td>
                      <td style={{ padding: '8px 4px', textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                        Rp {correct.toLocaleString('id-ID')}
                      </td>
                      <td style={{ padding: '8px 0', textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: 12, fontWeight: 700, color: Math.abs(diff) < 100 ? '#10b981' : diff > 0 ? '#dc2626' : '#10b981' }}>
                        {diff === 0 ? '–' : (diff > 0 ? '+' : '') + 'Rp ' + Math.abs(diff).toLocaleString('id-ID')}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Premium blurred */}
          <BlurredPremiumSection onUpgrade={() => onNavigate('pricing')} />

          {/* Actions */}
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <button onClick={() => { setStage('IDLE'); setVerdictData(null); }} style={{
              flex: 1, padding: '12px', borderRadius: 8, border: '1.5px solid var(--border)',
              background: 'var(--card)', color: 'var(--foreground)', fontSize: 14, fontWeight: 600, cursor: 'pointer',
            }}>Cek Slip Lain</button>
            <button onClick={() => setStage('FORM')} style={{
              flex: 1, padding: '12px', borderRadius: 8, border: 'none',
              background: '#10b981', color: '#fff', fontSize: 14, fontWeight: 600, cursor: 'pointer',
            }}>Hitung Ulang</button>
            <button style={{
              padding: '12px 16px', borderRadius: 8, border: '1.5px solid #f59e0b',
              background: '#fffbeb', color: '#d97706', fontSize: 13, fontWeight: 700, cursor: 'pointer',
            }}>📤 Bagikan</button>
          </div>

          {/* Cross-tool nudge */}
          {!isClean && (
            <button onClick={() => onNavigate('wajar-gaji')} style={{
              display: 'block', width: '100%', marginTop: 16, padding: '12px 16px',
              border: '1px solid var(--border)', borderRadius: 10,
              background: 'var(--muted)', cursor: 'pointer', textAlign: 'left', fontSize: 13,
            }}>
              💡 Cek juga standar gaji untuk posisimu →{' '}
              <span style={{ color: '#3b82f6', fontWeight: 600 }}>Wajar Gaji</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  // FORM state
  return (
    <div data-tool="wajar-slip" style={{ minHeight: '80vh', background: '#fffbeb', padding: '32px 0' }}>
      <div style={{ maxWidth: 560, margin: '0 auto', padding: '0 20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <h1 style={{ fontSize: 18, fontWeight: 800, color: 'var(--foreground)' }}>Konfirmasi Data Slip</h1>
            <p style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>Pastikan angka-angka sesuai slip gajimu</p>
          </div>
          <button onClick={() => setStage('IDLE')} style={{ background: 'none', border: 'none', color: 'var(--muted-foreground)', cursor: 'pointer', fontSize: 13 }}>✕ Batal</button>
        </div>

        <Steps current={1} />

        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, padding: '20px' }}>
          {/* Disclaimer */}
          <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 8, padding: '10px 14px', marginBottom: 20, fontSize: 12, color: '#1e40af' }}>
            ℹ️ Kalkulasi berdasarkan PMK 168/2023 (TER). Tidak menggantikan konsultasi pajak resmi.
          </div>

          <Field label="Gaji Bruto /bulan" hint="Sebelum potongan" error={errors.gross}>
            <Inp placeholder="7.500.000" {...idrInput(gross, setGross)} />
          </Field>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Field label="Status PTKP">
              <Sel value={ptkp} onChange={setPtkp} options={PTKP_OPTIONS} />
            </Field>
            <Field label="Kota" error={errors.city}>
              <Sel value={city} onChange={setCity} options={CITIES} />
            </Field>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Field label="Bulan">
              <Sel value={month} onChange={m => {}} options={MONTHS.map((l, i) => ({ value: String(i+1), label: l }))} />
            </Field>
            <Field label="NPWP">
              <div style={{ display: 'flex', gap: 16, height: 48, alignItems: 'center' }}>
                {[true, false].map(v => (
                  <label key={String(v)} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, cursor: 'pointer' }}>
                    <input type="radio" checked={hasNPWP === v} onChange={() => setHasNPWP(v)} style={{ accentColor: '#10b981' }} />
                    {v ? 'Ya' : 'Tidak'}
                  </label>
                ))}
              </div>
            </Field>
          </div>

          <div style={{ borderTop: '1px solid var(--border)', margin: '4px 0 16px' }} />
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 12 }}>Dari Slip Gaji</div>

          <Field label="PPh21 Dipotong">
            <Inp placeholder="112.500" {...idrInput(pph21, setPph21)} />
          </Field>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Field label="JHT Karyawan">
              <Inp placeholder="150.000" {...idrInput(jht, setJht)} />
            </Field>
            <Field label="JP Karyawan">
              <Inp placeholder="75.000" {...idrInput(jp, setJp)} />
            </Field>
          </div>

          <Field label="BPJS Kesehatan">
            <Inp placeholder="75.000" {...idrInput(kes, setKes)} />
          </Field>

          <Field label="Take Home Pay" optional>
            <Inp placeholder="7.000.000" {...idrInput(takeHome, setTakeHome)} />
          </Field>

          <button onClick={runCalculation} style={{
            width: '100%', padding: '14px', borderRadius: 10,
            border: 'none', background: '#10b981', color: '#fff',
            fontSize: 15, fontWeight: 700, cursor: 'pointer', marginTop: 4,
          }}>
            Cek Slip Gaji →
          </button>
        </div>

        <p style={{ textAlign: 'center', fontSize: 11, color: 'var(--muted-foreground)', marginTop: 14 }}>
          Kalkulasi berdasarkan PMK 168/2023 (TER). Hasil bukan pengganti konsultasi pajak resmi.
        </p>
      </div>
    </div>
  );
}


export default WajarSlipPage
