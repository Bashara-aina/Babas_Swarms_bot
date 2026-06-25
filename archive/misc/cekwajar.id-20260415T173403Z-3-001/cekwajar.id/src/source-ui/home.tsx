// @ts-nocheck
'use client'
import React, { useState, useEffect, useRef } from 'react'


// Shared UI + Homepage — exported to window
// ─── Formatters ───────────────────────────────────────────────────────────────

function fmtIDR(n) {
  if (!n && n !== 0) return '–';
  return 'Rp\u00a0' + n.toLocaleString('id-ID');
}
function fmtIDRShort(n) {
  if (!n) return '–';
  if (n >= 1_000_000) return 'Rp\u00a0' + (n / 1_000_000).toFixed(1).replace('.', ',') + ' jt';
  return fmtIDR(n);
}

// ─── Confidence Badge ─────────────────────────────────────────────────────────

function ConfidenceBadge({ level = 'Tinggi', source = 'BPS + 312 laporan', updated = '3 Apr 2026' }) {
  const dotColor = level === 'Tinggi' ? '#10b981' : level === 'Sedang' ? '#f59e0b' : '#94a3b8';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      fontSize: 11, fontFamily: 'var(--font-mono)',
      color: 'var(--muted-foreground)',
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: dotColor, flexShrink: 0 }} />
      {level} · {source} · Diperbarui {updated}
    </span>
  );
}

// ─── Verdict Card ─────────────────────────────────────────────────────────────

const VERDICT_STYLES = {
  WAJAR:           { color: '#16a34a', bg: 'rgba(22,163,74,0.05)',  border: '#16a34a', label: 'WAJAR' },
  DI_ATAS:         { color: '#16a34a', bg: 'rgba(22,163,74,0.05)',  border: '#16a34a', label: 'DI ATAS PASARAN' },
  SESUAI:          { color: '#16a34a', bg: 'rgba(22,163,74,0.05)',  border: '#16a34a', label: 'SESUAI' },
  PERLU_DICEK:     { color: '#d97706', bg: 'rgba(217,119,6,0.05)',  border: '#d97706', label: 'PERLU DICEK' },
  ADA_PELANGGARAN: { color: '#dc2626', bg: 'rgba(220,38,38,0.05)',  border: '#dc2626', label: 'ADA PELANGGARAN' },
  TIDAK_WAJAR:     { color: '#dc2626', bg: 'rgba(220,38,38,0.05)',  border: '#dc2626', label: 'TIDAK WAJAR' },
  DI_BAWAH:        { color: '#dc2626', bg: 'rgba(220,38,38,0.05)',  border: '#dc2626', label: 'DI BAWAH PASARAN' },
};

function VerdictCard({ type, sentence, confidenceProps, children }) {
  const s = VERDICT_STYLES[type] || VERDICT_STYLES.WAJAR;
  return (
    <div className="animate-fade-in-up" style={{
      borderLeft: `4px solid ${s.border}`,
      background: s.bg,
      borderRadius: '0 12px 12px 0',
      padding: '20px 20px 20px 24px',
      marginBottom: 20,
    }}>
      <div style={{
        fontSize: 'clamp(1.5rem, 4vw, 2.25rem)',
        fontWeight: 800, color: s.color,
        letterSpacing: '-0.02em', lineHeight: 1.1,
        marginBottom: 8,
      }}>{s.label}</div>
      {sentence && (
        <div style={{ fontSize: 15, color: 'var(--muted-foreground)', lineHeight: 1.5, marginBottom: 10 }}>
          {sentence}
        </div>
      )}
      {confidenceProps && <ConfidenceBadge {...confidenceProps} />}
      {children}
    </div>
  );
}

// ─── Blurred Premium Block ────────────────────────────────────────────────────

function BlurredPremiumSection({ onUpgrade }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--foreground)', marginBottom: 12 }}>
        Kenapa hasilnya begini?
      </div>
      {[
        { label: 'Tren gaji 12 bulan terakhir', h: 72 },
        { label: 'Breakdown per ukuran perusahaan', h: 56 },
        { label: 'Template negosiasi untuk posisi ini', h: 64 },
      ].map(({ label, h }) => (
        <div key={label} style={{ position: 'relative', marginBottom: 10, borderRadius: 10, overflow: 'hidden' }}>
          <div style={{
            height: h, background: 'var(--muted)', borderRadius: 10,
            filter: 'blur(4px)', opacity: 0.6,
            backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 20px, rgba(0,0,0,0.03) 20px, rgba(0,0,0,0.03) 21px)',
          }} />
          <div style={{
            position: 'absolute', inset: 0, display: 'flex', alignItems: 'center',
            justifyContent: 'center', backdropFilter: 'blur(2px)',
          }}>
            <span style={{ fontSize: 12, color: 'var(--muted-foreground)', fontWeight: 500 }}>🔒 {label}</span>
          </div>
        </div>
      ))}
      {/* Upgrade card */}
      <div onClick={onUpgrade} style={{
        border: '1.5px solid var(--border)', borderRadius: 12, padding: '16px 20px',
        cursor: 'pointer', transition: 'border-color 150ms',
        background: 'var(--card)',
      }}
      onMouseEnter={e => e.currentTarget.style.borderColor = '#10b981'}
      onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
      >
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--foreground)', marginBottom: 4 }}>
          Lihat mengapa hasilnya begini — dan cara naiknya.
        </div>
        <div style={{
          display: 'inline-block', marginTop: 8,
          padding: '8px 16px', borderRadius: 8, background: '#10b981',
          fontSize: 13, fontWeight: 600, color: '#fff',
        }}>
          Buka dengan Pro — Rp 49.000/bulan
        </div>
        <div style={{ fontSize: 11, color: 'var(--muted-foreground)', marginTop: 6 }}>
          Batalkan kapan saja · Tanpa kontrak
        </div>
      </div>
    </div>
  );
}

// ─── Salary Range Bar ─────────────────────────────────────────────────────────

function SalaryRangeBar({ p10, p50, p90, userSalary }) {
  const min = p10;
  const max = p90;
  const range = max - min;
  const p50pct = ((p50 - min) / range * 100).toFixed(1);
  const userPct = userSalary != null ? Math.min(100, Math.max(0, (userSalary - min) / range * 100)).toFixed(1) : null;
  const gap = userSalary ? ((userSalary - p50) / p50 * 100).toFixed(0) : null;

  return (
    <div style={{ marginBottom: 16 }}>
      {/* Labels */}
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--muted-foreground)', marginBottom: 6, fontFamily: 'var(--font-mono)' }}>
        <span>P10 · {fmtIDRShort(p10)}</span>
        <span style={{ fontWeight: 600, color: 'var(--foreground)' }}>Median</span>
        <span>P90 · {fmtIDRShort(p90)}</span>
      </div>
      {/* Bar */}
      <div style={{ position: 'relative', height: 28, background: 'var(--muted)', borderRadius: 99 }}>
        {/* Filled range */}
        <div style={{
          position: 'absolute', top: 0, bottom: 0,
          left: '10%', right: '10%',
          background: 'rgba(16,185,129,0.12)', borderRadius: 99,
        }} />
        {/* Median line */}
        <div style={{
          position: 'absolute', top: 4, bottom: 4, width: 3,
          left: `calc(${p50pct}% - 1.5px)`,
          background: '#10b981', borderRadius: 99,
        }} />
        {/* User dot */}
        {userPct !== null && (
          <div style={{
            position: 'absolute', top: '50%', transform: 'translate(-50%, -50%)',
            left: `${userPct}%`,
            width: 16, height: 16, borderRadius: '50%',
            background: gap > 0 ? '#dc2626' : '#16a34a',
            border: '2.5px solid #fff',
            boxShadow: '0 0 0 2px ' + (gap > 0 ? '#dc2626' : '#16a34a'),
            zIndex: 2,
          }} />
        )}
      </div>
      {/* Key numbers */}
      <div style={{
        display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap',
      }}>
        {[
          { label: 'P10', val: fmtIDRShort(p10) },
          { label: 'Median', val: fmtIDRShort(p50), bold: true },
          { label: 'P90', val: fmtIDRShort(p90) },
          ...(userSalary ? [{ label: 'Kamu', val: fmtIDRShort(userSalary), accent: true }] : []),
          ...(gap ? [{ label: 'Gap', val: (gap > 0 ? '+' : '') + gap + '%', color: gap > 0 ? '#16a34a' : '#dc2626' }] : []),
        ].map(({ label, val, bold, accent, color }) => (
          <div key={label} style={{
            flex: '1 1 auto', minWidth: 64,
            background: 'var(--muted)', borderRadius: 8, padding: '8px 10px',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: 10, color: 'var(--muted-foreground)', marginBottom: 2, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</div>
            <div style={{ fontSize: 13, fontWeight: bold || accent ? 700 : 500, color: color || (accent ? '#10b981' : 'var(--foreground)'), fontFamily: 'var(--font-mono)' }}>{val}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Homepage ─────────────────────────────────────────────────────────────────

export default function HomePage({ onNavigate }) {
  const [count] = useState(287 + Math.floor(Math.random() * 40));

  const testimonials = [
    { quote: 'Baru tau ternyata JHT aku kurang dipotong. Langsung tanya ke HR deh.', name: 'Dita Rahayu', title: 'Marketing Manager, Surabaya' },
    { quote: 'Pas dapat offer kerja baru, langsung cek di Wajar Gaji. Jadi lebih pede nego gaji.', name: 'Rizky Pratama', title: 'Software Engineer, Bandung' },
    { quote: 'Simpel banget. Upload slip, 30 detik langsung tau ada masalah nggak.', name: 'Sari Dewi', title: 'Akuntan, Jakarta Selatan' },
  ];

  return (
    <div>
      {/* Hero */}
      <section style={{
        background: 'linear-gradient(160deg, #ecfdf5 0%, var(--background) 60%)',
        padding: 'clamp(48px, 8vw, 96px) 24px clamp(40px, 6vw, 72px)',
        position: 'relative', overflow: 'hidden',
      }}>
        {/* BG watermark */}
        <div style={{
          position: 'absolute', right: -40, top: -20, width: 320, height: 320,
          opacity: 0.04, pointerEvents: 'none',
          fontSize: 280, lineHeight: 1, userSelect: 'none',
        }}>⚖️</div>

        <div style={{ maxWidth: 680, margin: '0 auto', position: 'relative', textAlign: 'center' }}>
          {/* Trust pill */}
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            background: 'var(--card)', border: '1px solid #a7f3d0',
            borderRadius: 99, padding: '6px 14px',
            fontSize: 12, color: '#059669', fontWeight: 500,
            marginBottom: 24, boxShadow: '0 1px 6px rgba(16,185,129,0.08)',
          }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#10b981' }} />
            Gratis · Berbasis PMK 168/2023 · Data Terenkripsi
          </div>

          {/* Headline */}
          <h1 style={{
            fontSize: 'clamp(2rem, 5vw, 3.25rem)', fontWeight: 800,
            letterSpacing: '-0.03em', lineHeight: 1.1,
            color: 'var(--foreground)', marginBottom: 16,
            textWrap: 'pretty',
          }}>
            Slip gaji kamu dipotong{' '}
            <span style={{ color: '#10b981', display: 'block' }}>sesuai aturan nggak?</span>
          </h1>

          <p style={{
            fontSize: 'clamp(1rem, 2vw, 1.2rem)',
            color: 'var(--muted-foreground)', lineHeight: 1.6,
            maxWidth: 480, margin: '0 auto 28px',
          }}>
            Audit PPh21 dan BPJS dalam 30 detik. Gratis. Tanpa daftar.
          </p>

          {/* CTAs */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, justifyContent: 'center', marginBottom: 16 }}>
            <button onClick={() => onNavigate('wajar-slip')} style={{
              padding: '13px 28px', borderRadius: 10, border: 'none',
              background: '#10b981', color: '#fff', fontSize: 15, fontWeight: 700,
              cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8,
            }}>
              Cek Slip Gaji Sekarang →
            </button>
            <button onClick={() => onNavigate('wajar-gaji')} style={{
              padding: '13px 24px', borderRadius: 10,
              border: '1.5px solid var(--border)', background: 'var(--card)',
              color: 'var(--foreground)', fontSize: 15, fontWeight: 600,
              cursor: 'pointer',
            }}>
              Cek Standar Gaji
            </button>
          </div>

          {/* Social proof */}
          <p style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>
            Sudah{' '}
            <span style={{ fontWeight: 700, color: 'var(--foreground)', fontFamily: 'var(--font-mono)' }}>
              {count.toLocaleString('id-ID')}
            </span>
            {' '}slip gaji dicek minggu ini
          </p>
        </div>
      </section>

      {/* Decision helper */}
      <section style={{ padding: '32px 24px 20px', maxWidth: 640, margin: '0 auto' }}>
        <p style={{ textAlign: 'center', fontSize: 12, fontWeight: 600, color: 'var(--muted-foreground)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 14 }}>
          Mulai dari mana?
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 10 }}>
          {[
            { href: 'wajar-slip', q: 'Punya slip gaji?', action: 'Audit sekarang →', bg: '#fffbeb', border: '#fde68a', dot: '#f59e0b' },
            { href: 'wajar-gaji', q: 'Dapat tawaran kerja?', action: 'Benchmark gaji →', bg: '#eff6ff', border: '#bfdbfe', dot: '#3b82f6' },
            { href: 'wajar-kabur', q: 'Mau kerja di LN?', action: 'Hitung daya beli →', bg: '#eef2ff', border: '#c7d2fe', dot: '#6366f1' },
          ].map(({ href, q, action, bg, border, dot }) => (
            <button key={href} onClick={() => onNavigate(href)} style={{
              padding: '14px 14px 12px',
              border: `1.5px solid ${border}`,
              borderRadius: 12,
              background: bg,
              cursor: 'pointer', textAlign: 'left',
              transition: 'all 150ms',
            }}
            onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-1px)'; e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.07)'; }}
            onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; }}
            >
              <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', marginBottom: 4 }}>{q}</div>
              <div style={{ fontSize: 12, color: dot, fontWeight: 700 }}>{action}</div>
            </button>
          ))}
        </div>
      </section>

      {/* Wajar Slip featured */}
      <section style={{ padding: '16px 24px 24px', maxWidth: 720, margin: '0 auto' }}>
        <div style={{
          border: '2px solid #a7f3d0', borderRadius: 16,
          background: 'linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%)',
          padding: '24px',
          cursor: 'pointer',
        }} onClick={() => onNavigate('wajar-slip')}
        onMouseEnter={e => e.currentTarget.style.borderColor = '#10b981'}
        onMouseLeave={e => e.currentTarget.style.borderColor = '#a7f3d0'}
        >
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16, flexWrap: 'wrap' }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: '#10b981', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>⭐ Alat Utama</div>
              <h2 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', marginBottom: 6 }}>Wajar Slip — Audit Slip Gaji</h2>
              <p style={{ fontSize: 13, color: '#64748b', marginBottom: 16, lineHeight: 1.6 }}>
                Deteksi 7 jenis pelanggaran PPh21, BPJS, dan UMK. Upload foto atau PDF slip gajimu.
              </p>
              <div style={{
                fontSize: 14, fontWeight: 700, color: '#059669',
                display: 'flex', alignItems: 'center', gap: 4,
              }}>Mulai Audit Gratis →</div>
            </div>

            {/* Mock result preview */}
            <div style={{
              background: '#fff', borderRadius: 12, padding: '14px 16px',
              border: '1px solid #d1fae5', minWidth: 180, boxShadow: '0 2px 12px rgba(0,0,0,0.05)',
            }}>
              <div style={{ fontSize: 9, color: '#94a3b8', fontFamily: 'var(--font-mono)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.06em' }}>Contoh Hasil</div>
              <div style={{ fontSize: 15, fontWeight: 800, color: '#dc2626', marginBottom: 2 }}>ADA PELANGGARAN</div>
              <div style={{ fontSize: 11, color: '#64748b', marginBottom: 10 }}>JHT kurang dipotong Rp 150.000</div>
              <div style={{
                background: '#fee2e2', borderRadius: 6, padding: '6px 8px',
                fontSize: 11, color: '#dc2626', fontWeight: 600,
              }}>2 pelanggaran ditemukan</div>
              <div style={{ marginTop: 8, fontSize: 10, color: '#94a3b8', fontFamily: 'var(--font-mono)' }}>● Tinggi · PMK 168/2023</div>
            </div>
          </div>
        </div>
      </section>

      {/* Tool grid 2×2 */}
      <section style={{ padding: '0 24px 40px', maxWidth: 720, margin: '0 auto' }}>
        <p style={{ fontSize: 11, fontWeight: 600, color: 'var(--muted-foreground)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>Juga tersedia</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 10 }}>
          {[
            { id: 'wajar-gaji', name: 'Wajar Gaji', desc: 'Benchmark gaji posisimu', color: '#3b82f6', bg: '#eff6ff', border: '#bfdbfe' },
            { id: 'wajar-tanah', name: 'Wajar Tanah', desc: 'Harga tanah & properti', color: '#78716c', bg: '#fafaf9', border: '#e7e5e4' },
            { id: 'wajar-kabur', name: 'Wajar Kabur', desc: 'Daya beli luar negeri', color: '#6366f1', bg: '#eef2ff', border: '#c7d2fe' },
            { id: 'wajar-hidup', name: 'Wajar Hidup', desc: 'Biaya hidup antar kota', color: '#14b8a6', bg: '#f0fdfa', border: '#99f6e4' },
          ].map(({ id, name, desc, color, bg, border }) => (
            <button key={id} onClick={() => onNavigate(id)} style={{
              padding: '14px', borderRadius: 12,
              border: `1.5px solid ${border}`,
              background: bg, cursor: 'pointer', textAlign: 'left',
              transition: 'all 150ms',
            }}
            onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 4px 16px rgba(0,0,0,0.07)'; }}
            onMouseLeave={e => { e.currentTarget.style.transform = ''; e.currentTarget.style.boxShadow = ''; }}
            >
              <div style={{ fontSize: 13, fontWeight: 700, color, marginBottom: 3 }}>{name}</div>
              <div style={{ fontSize: 11, color: '#64748b' }}>{desc}</div>
              <div style={{ fontSize: 11, color, marginTop: 8, fontWeight: 600 }}>Cek →</div>
            </button>
          ))}
        </div>
      </section>

      {/* Testimonials */}
      <section style={{
        padding: '40px 24px',
        background: 'var(--muted)',
        borderTop: '1px solid var(--border)',
      }}>
        <div style={{ maxWidth: 720, margin: '0 auto' }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--foreground)', marginBottom: 20 }}>
            Apa kata mereka
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14 }}>
            {testimonials.map(({ quote, name, title }) => (
              <div key={name} style={{
                background: 'var(--card)', borderRadius: 12, padding: '18px',
                border: '1px solid var(--border)',
              }}>
                <p style={{ fontSize: 13, color: 'var(--foreground)', lineHeight: 1.6, marginBottom: 12, fontStyle: 'italic' }}>
                  "{quote}"
                </p>
                <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--foreground)' }}>{name}</div>
                <div style={{ fontSize: 11, color: 'var(--muted-foreground)' }}>{title}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Data sources strip */}
      <section style={{
        padding: '16px 24px',
        borderTop: '1px solid var(--border)',
        textAlign: 'center',
      }}>
        <p style={{ fontSize: 11, color: 'var(--muted-foreground)', fontFamily: 'var(--font-mono)' }}>
          Data dari BPS · Kemnaker · BPN · Diperbarui setiap hari
        </p>
      </section>
    </div>
  );
}


export { VerdictCard, BlurredPremiumSection, SalaryRangeBar, ConfidenceBadge, fmtIDR, fmtIDRShort, VERDICT_STYLES }
