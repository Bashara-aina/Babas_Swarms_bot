const { useState, useEffect, useRef, useCallback } = React;

// ─── nav ───

// GlobalNav + Footer — exported to window



function GlobalNav({ currentPage, onNavigate, darkMode, onToggleDark }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const tools = [
    { id: 'wajar-slip', name: 'Wajar Slip', dot: '#f59e0b' },
    { id: 'wajar-gaji', name: 'Wajar Gaji', dot: '#3b82f6' },
    { id: 'wajar-tanah', name: 'Wajar Tanah', dot: '#78716c' },
    { id: 'wajar-kabur', name: 'Wajar Kabur', dot: '#6366f1' },
    { id: 'wajar-hidup', name: 'Wajar Hidup', dot: '#14b8a6' },
  ];

  return (
    <header style={{
      position: 'sticky', top: 0, zIndex: 50, width: '100%',
      backgroundColor: 'var(--nav-bg)',
      borderBottom: `1px solid var(--nav-border)`,
      boxShadow: scrolled ? '0 1px 12px rgba(0,0,0,0.06)' : 'none',
      transition: 'box-shadow 200ms'
    }}>
      <nav style={{
        maxWidth: 1024, margin: '0 auto',
        height: 56, padding: '0 20px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        {/* Logo */}
        <button onClick={() => onNavigate('home')} style={{
          display: 'flex', alignItems: 'center', gap: 8,
          background: 'none', border: 'none', cursor: 'pointer', padding: 0,
        }}>
          <span style={{
            width: 28, height: 28, borderRadius: 8,
            background: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 2L3 6h2v6h6V6h2L8 2z" fill="white" opacity="0.9"/>
              <rect x="2" y="12" width="12" height="1.5" rx="0.75" fill="white" opacity="0.7"/>
            </svg>
          </span>
          <span style={{ fontWeight: 700, fontSize: 16, color: 'var(--foreground)', letterSpacing: '-0.02em' }}>
            cekwajar<span style={{ color: '#10b981' }}>.id</span>
          </span>
        </button>

        {/* Desktop tool links */}
        <div className="desktop-nav" style={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {tools.map(tool => (
            <button key={tool.id} onClick={() => onNavigate(tool.id)} style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 12px', borderRadius: 6, border: 'none', cursor: 'pointer',
              fontSize: 13, fontWeight: 500,
              background: currentPage === tool.id ? 'rgba(16,185,129,0.1)' : 'transparent',
              color: currentPage === tool.id ? '#059669' : 'var(--nav-text-muted)',
              transition: 'all 150ms',
            }}
            onMouseEnter={e => { if (currentPage !== tool.id) e.currentTarget.style.background = 'var(--nav-hover-bg)'; }}
            onMouseLeave={e => { if (currentPage !== tool.id) e.currentTarget.style.background = 'transparent'; }}
            >
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: tool.dot, flexShrink: 0 }} />
              {tool.name}
            </button>
          ))}
        </div>

        {/* Right actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button onClick={onToggleDark} style={{
            width: 36, height: 36, borderRadius: 8, border: '1px solid var(--border)',
            background: 'transparent', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--nav-text-muted)',
          }}>
            {darkMode ? '☀️' : '🌙'}
          </button>
          <button onClick={() => onNavigate('pricing')} style={{
            padding: '7px 16px', borderRadius: 8, border: '1.5px solid #10b981',
            background: 'transparent', cursor: 'pointer', fontSize: 13, fontWeight: 600,
            color: '#059669',
          }}>
            Masuk
          </button>
          <button onClick={() => onNavigate('wajar-slip')} className="hide-mobile" style={{
            padding: '7px 16px', borderRadius: 8, border: 'none',
            background: '#10b981', cursor: 'pointer', fontSize: 13, fontWeight: 600,
            color: '#fff',
          }}>
            Cek Gratis
          </button>

          {/* Mobile hamburger */}
          <button className="show-mobile" onClick={() => setMobileOpen(v => !v)} style={{
            width: 36, height: 36, borderRadius: 8, border: '1px solid var(--border)',
            background: 'transparent', cursor: 'pointer', fontSize: 18,
            display: 'none', alignItems: 'center', justifyContent: 'center',
          }}>
            {mobileOpen ? '✕' : '☰'}
          </button>
        </div>
      </nav>

      {/* Mobile menu */}
      {mobileOpen && (
        <div style={{
          borderTop: '1px solid var(--border)',
          background: 'var(--nav-bg)',
          padding: '12px 20px 16px',
        }}>
          {tools.map(tool => (
            <button key={tool.id} onClick={() => { onNavigate(tool.id); setMobileOpen(false); }} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              width: '100%', padding: '12px 0', border: 'none', background: 'transparent',
              cursor: 'pointer', fontSize: 15, fontWeight: 500,
              color: currentPage === tool.id ? '#059669' : 'var(--foreground)',
              borderBottom: '1px solid var(--border)',
            }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: tool.dot }} />
              {tool.name}
            </button>
          ))}
          <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
            <button onClick={() => { onNavigate('pricing'); setMobileOpen(false); }} style={{
              flex: 1, padding: '12px', borderRadius: 8, border: '1.5px solid #10b981',
              background: 'transparent', cursor: 'pointer', fontSize: 14, fontWeight: 600, color: '#059669',
            }}>Masuk</button>
            <button onClick={() => { onNavigate('wajar-slip'); setMobileOpen(false); }} style={{
              flex: 1, padding: '12px', borderRadius: 8, border: 'none',
              background: '#10b981', cursor: 'pointer', fontSize: 14, fontWeight: 600, color: '#fff',
            }}>Cek Gratis</button>
          </div>
        </div>
      )}
    </header>
  );
}

function SiteFooter({ onNavigate }) {
  return (
    <footer style={{
      borderTop: '1px solid var(--border)',
      padding: '32px 24px',
      marginTop: 'auto',
    }}>
      <div style={{ maxWidth: 1024, margin: '0 auto' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 32, justifyContent: 'space-between', marginBottom: 24 }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--foreground)', marginBottom: 6 }}>
              cekwajar<span style={{ color: '#10b981' }}>.id</span>
            </div>
            <div style={{ fontSize: 12, color: 'var(--muted-foreground)', maxWidth: 240, lineHeight: 1.6 }}>
              Transparansi keuangan untuk semua orang Indonesia.
            </div>
          </div>
          <div style={{ display: 'flex', gap: 48 }}>
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--muted-foreground)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>Alat</div>
              {['wajar-slip','wajar-gaji','wajar-tanah','wajar-kabur','wajar-hidup'].map(t => (
                <button key={t} onClick={() => onNavigate(t)} style={{
                  display: 'block', background: 'none', border: 'none', cursor: 'pointer',
                  fontSize: 13, color: 'var(--muted-foreground)', padding: '3px 0',
                  textAlign: 'left',
                }}>
                  {t.replace('wajar-', 'Wajar ').replace(/\b\w/g, c => c.toUpperCase())}
                </button>
              ))}
            </div>
            <div>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--muted-foreground)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 10 }}>Lainnya</div>
              {['Pricing','Kontak','Privacy','Terms'].map(t => (
                <button key={t} onClick={() => t === 'Pricing' && onNavigate('pricing')} style={{
                  display: 'block', background: 'none', border: 'none', cursor: 'pointer',
                  fontSize: 13, color: 'var(--muted-foreground)', padding: '3px 0',
                  textAlign: 'left',
                }}>{t}</button>
              ))}
            </div>
          </div>
        </div>
        <div style={{
          borderTop: '1px solid var(--border)', paddingTop: 16,
          display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'space-between', alignItems: 'center',
        }}>
          <div style={{ fontSize: 11, color: 'var(--muted-foreground)', fontFamily: 'var(--font-mono)' }}>
            Data dari BPS · Kemnaker · BPN · Diperbarui setiap hari
          </div>
          <div style={{ fontSize: 11, color: 'var(--muted-foreground)' }}>
            © 2026 cekwajar.id
          </div>
        </div>
      </div>
    </footer>
  );
}




// ─── home ───

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

function HomePage({ onNavigate }) {
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




// ─── slip ───

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
              −{window.fmtIDR ? window.fmtIDR(diff) : `Rp ${diff.toLocaleString('id-ID')}`}
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
            <window.VerdictCard
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
          <window.BlurredPremiumSection onUpgrade={() => onNavigate('pricing')} />

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




// ─── tanah ───

// Wajar Tanah — full implementation

const PROVINCES = ['DKI Jakarta','Jawa Barat','Jawa Timur','Jawa Tengah','Banten','Bali','Sumatera Utara','Sulawesi Selatan','Kalimantan Timur','DI Yogyakarta'];

const CITIES_BY_PROV = {
  'DKI Jakarta': ['Jakarta Pusat','Jakarta Selatan','Jakarta Barat','Jakarta Timur','Jakarta Utara'],
  'Jawa Barat': ['Bandung','Bekasi','Depok','Bogor','Cimahi','Sukabumi'],
  'Jawa Timur': ['Surabaya','Malang','Sidoarjo','Gresik','Mojokerto'],
  'Jawa Tengah': ['Semarang','Solo','Magelang','Salatiga'],
  'Banten': ['Tangerang','Tangerang Selatan','Serang','Cilegon'],
  'Bali': ['Denpasar','Badung','Gianyar','Tabanan','Buleleng'],
  'Sumatera Utara': ['Medan','Binjai','Pematang Siantar'],
  'Sulawesi Selatan': ['Makassar','Gowa','Maros'],
  'Kalimantan Timur': ['Balikpapan','Samarinda','Bontang'],
  'DI Yogyakarta': ['Yogyakarta','Sleman','Bantul','Kulon Progo'],
};

const KECAMATAN_BY_CITY = {
  'Jakarta Selatan': ['Kebayoran Baru','Mampang Prapatan','Pesanggrahan','Tebet','Pancoran'],
  'Jakarta Pusat': ['Menteng','Gambir','Tanah Abang','Senen','Cempaka Putih'],
  'Jakarta Barat': ['Kebon Jeruk','Palmerah','Tambora','Cengkareng'],
  'Jakarta Timur': ['Jatinegara','Kramat Jati','Matraman','Pulo Gadung'],
  'Jakarta Utara': ['Penjaringan','Pademangan','Tanjung Priok','Koja'],
  'Bandung': ['Coblong','Cicendo','Sukasari','Antapani','Buah Batu'],
  'Bekasi': ['Bekasi Utara','Bekasi Selatan','Bekasi Barat','Bekasi Timur','Jatiasih'],
  'Surabaya': ['Gubeng','Wonokromo','Rungkut','Sukolilo','Mulyorejo'],
  'Denpasar': ['Denpasar Selatan','Denpasar Barat','Denpasar Timur','Denpasar Utara'],
  'Badung': ['Kuta','Kuta Selatan','Mengwi','Kuta Utara'],
  'Tangerang Selatan': ['Serpong','Pamulang','Ciputat','Pondok Aren'],
  'Yogyakarta': ['Gondokusuman','Umbulharjo','Danurejan','Jetis','Mergangsan'],
  'Sleman': ['Depok','Mlati','Gamping','Godean'],
  'Malang': ['Lowokwaru','Blimbing','Kedungkandang','Klojen'],
};

// Price benchmarks per m² (in thousands IDR) by city + type
const PRICE_BENCH = {
  'Jakarta Selatan': { tanah: 45000000, rumah: 32000000, apartemen: 40000000, ruko: 55000000 },
  'Jakarta Pusat':   { tanah: 60000000, rumah: 45000000, apartemen: 55000000, ruko: 70000000 },
  'Jakarta Barat':   { tanah: 28000000, rumah: 22000000, apartemen: 30000000, ruko: 38000000 },
  'Jakarta Timur':   { tanah: 22000000, rumah: 18000000, apartemen: 25000000, ruko: 32000000 },
  'Jakarta Utara':   { tanah: 30000000, rumah: 24000000, apartemen: 28000000, ruko: 40000000 },
  'Bandung':         { tanah: 12000000, rumah: 9000000, apartemen: 15000000, ruko: 18000000 },
  'Bekasi':          { tanah: 8000000,  rumah: 7000000, apartemen: 12000000, ruko: 14000000 },
  'Surabaya':        { tanah: 15000000, rumah: 12000000, apartemen: 18000000, ruko: 22000000 },
  'Denpasar':        { tanah: 20000000, rumah: 16000000, apartemen: 22000000, ruko: 28000000 },
  'Badung':          { tanah: 35000000, rumah: 28000000, apartemen: 40000000, ruko: 45000000 },
  'Tangerang Selatan':{ tanah: 16000000, rumah: 14000000, apartemen: 20000000, ruko: 22000000 },
  'Yogyakarta':      { tanah: 8000000,  rumah: 7000000, apartemen: 10000000, ruko: 12000000 },
  'Malang':          { tanah: 6000000,  rumah: 5500000, apartemen: 8000000, ruko: 10000000 },
};

const DEFAULT_BENCH = { tanah: 5000000, rumah: 4500000, apartemen: 7000000, ruko: 9000000 };

const PROP_TYPES = [
  { id: 'rumah', label: 'Rumah', icon: '🏠' },
  { id: 'tanah', label: 'Tanah', icon: '🌿' },
  { id: 'apartemen', label: 'Apartemen', icon: '🏢' },
  { id: 'ruko', label: 'Ruko', icon: '🏪' },
];

/* fmtIDR stripped */

/* const inputStyle stripped */

function FocusInput({ style, value, onChange, placeholder, disabled, type }) {
  const [f, setF] = useState(false);
  return <input type={type||'text'} value={value} onChange={onChange} placeholder={placeholder} disabled={disabled}
    style={{ ...inputStyle, ...(f ? { borderColor: '#78716c' } : {}), ...(disabled ? { opacity: 0.5, cursor: 'not-allowed' } : {}), ...style }}
    onFocus={() => setF(true)} onBlur={() => setF(false)} />;
}

function FocusSelect({ value, onChange, options, disabled, placeholder }) {
  const [f, setF] = useState(false);
  return (
    <select value={value} onChange={e => onChange(e.target.value)} disabled={disabled}
      style={{ ...inputStyle, ...(f ? { borderColor: '#78716c' } : {}), ...(disabled ? { opacity: 0.5, cursor: 'not-allowed' } : {}) }}
      onFocus={() => setF(true)} onBlur={() => setF(false)}
    >
      {placeholder && <option value="">{placeholder}</option>}
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  );
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
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          {[1,2].map(i => <div key={i}>{bar('100%', 64)}</div>)}
        </div>
      </div>
      <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, padding: 20 }}>
        {bar('100%', 100)}
      </div>
    </div>
  );
}

function WajarTanahPage({ onNavigate }) {
  const [stage, setStage] = useState('IDLE');
  const [province, setProvince] = useState('');
  const [city, setCity] = useState('');
  const [kecamatan, setKecamatan] = useState('');
  const [propType, setPropType] = useState('rumah');
  const [luas, setLuas] = useState('');
  const [harga, setHarga] = useState('');
  const [result, setResult] = useState(null);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [errors, setErrors] = useState({});

  const cities = province ? (CITIES_BY_PROV[province] || []) : [];
  const kecs = city ? (KECAMATAN_BY_CITY[city] || ['Kecamatan A','Kecamatan B','Kecamatan C']) : [];

  const pricePerSqm = harga && luas
    ? Math.round(parseInt(harga.replace(/\D/g,''),10) / parseInt(luas,10))
    : null;

  const fmtIDRInput = (val, setter) => ({
    value: val,
    onChange: e => {
      const raw = e.target.value.replace(/\D/g,'');
      setter(raw ? parseInt(raw,10).toLocaleString('id-ID') : '');
    }
  });

  const handleSubmit = () => {
    const errs = {};
    if (!province) errs.province = 'Pilih provinsi';
    if (!city) errs.city = 'Pilih kota';
    if (!luas || isNaN(parseInt(luas))) errs.luas = 'Masukkan luas properti';
    if (!harga) errs.harga = 'Masukkan harga yang ditawarkan';
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    setStage('LOADING');

    const msgs = [
      `Mencari data properti di ${city}...`,
      'Membandingkan dengan transaksi terakhir di area ini...',
      'Menghitung harga wajar berdasarkan NJOP dan ZNT...',
    ];
    let i = 0;
    setLoadingMsg(msgs[0]);
    const iv = setInterval(() => { i++; if (i < msgs.length) setLoadingMsg(msgs[i]); }, 800);

    setTimeout(() => {
      clearInterval(iv);
      const bench = PRICE_BENCH[city] || DEFAULT_BENCH;
      const medianPerSqm = bench[propType];
      const luasNum = parseInt(luas, 10);
      const hargaNum = parseInt(harga.replace(/\D/g,''), 10);
      const userPerSqm = Math.round(hargaNum / luasNum);
      const medianTotal = medianPerSqm * luasNum;
      const diffPct = Math.round((userPerSqm - medianPerSqm) / medianPerSqm * 100);

      let verdictType, verdictSentence;
      if (diffPct > 20) {
        verdictType = 'TERLALU_MAHAL';
        verdictSentence = `Harga yang ditawarkan ${diffPct}% di atas median pasar untuk ${propType} di ${city}.`;
      } else if (diffPct < -20) {
        verdictType = 'MURAH';
        verdictSentence = `Harga ini ${Math.abs(diffPct)}% di bawah median pasar — bisa jadi kesempatan bagus.`;
      } else {
        verdictType = 'WAJAR';
        verdictSentence = `Harga per m² sesuai dengan median pasar untuk ${propType} di ${city}.`;
      }

      setResult({ verdictType, verdictSentence, medianPerSqm, medianTotal, userPerSqm, diffPct, hargaNum, luasNum, city, propType, kecamatan });
      setStage('RESULT');
    }, 2800);
  };

  const accentColor = '#78716c';
  const tint = 'var(--background)';
  const bg = '#fafaf9';

  if (stage === 'LOADING') return (
    <div data-tool="wajar-tanah" style={{ minHeight: '80vh', background: bg, padding: '32px 0' }}>
      <div style={{ maxWidth: 560, margin: '0 auto', padding: '0 20px' }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ width: 48, height: 48, borderRadius: '50%', border: `4px solid #e7e5e4`, borderTopColor: accentColor, animation: 'spin 1s linear infinite', margin: '0 auto 16px' }} />
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--foreground)', marginBottom: 4 }}>{loadingMsg}</div>
          <div style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>Membandingkan dengan data BPN dan transaksi publik...</div>
        </div>
        <ResultSkeleton />
      </div>
    </div>
  );

  if (stage === 'RESULT' && result) {
    const { verdictType, verdictSentence, medianPerSqm, medianTotal, userPerSqm, diffPct, hargaNum, luasNum, city: c, propType: pt } = result;
    const VERDICT_MAP = {
      WAJAR:        { color: '#16a34a', bg: 'rgba(22,163,74,0.05)',  border: '#16a34a', label: 'WAJAR' },
      TERLALU_MAHAL:{ color: '#dc2626', bg: 'rgba(220,38,38,0.05)', border: '#dc2626', label: 'TERLALU MAHAL' },
      MURAH:        { color: '#2563eb', bg: 'rgba(37,99,235,0.05)', border: '#2563eb', label: 'DI BAWAH PASAR' },
    };
    const vs = VERDICT_MAP[verdictType] || VERDICT_MAP.WAJAR;

    return (
      <div data-tool="wajar-tanah" style={{ minHeight: '80vh', background: bg, padding: '32px 0' }}>
        <div style={{ maxWidth: 600, margin: '0 auto', padding: '0 20px' }}>
          <button onClick={() => { setStage('IDLE'); setResult(null); }} style={{ display: 'flex', alignItems: 'center', gap: 4, background: 'none', border: 'none', color: 'var(--muted-foreground)', cursor: 'pointer', fontSize: 13, marginBottom: 20 }}>← Cek lagi</button>

          {/* VERDICT — dominant */}
          <div className="animate-fade-in-up" style={{ borderLeft: `4px solid ${vs.border}`, background: vs.bg, borderRadius: '0 12px 12px 0', padding: '20px 20px 20px 24px', marginBottom: 16 }}>
            <div style={{ fontSize: 'clamp(1.5rem, 4vw, 2.25rem)', fontWeight: 800, color: vs.color, letterSpacing: '-0.02em', lineHeight: 1.1, marginBottom: 8 }}>{vs.label}</div>
            <div style={{ fontSize: 14, color: 'var(--muted-foreground)', lineHeight: 1.5, marginBottom: 10 }}>{verdictSentence}</div>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11, fontFamily: 'var(--font-mono)', color: 'var(--muted-foreground)' }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#78716c' }} />
              BPN + notaris + listing publik · Diperbarui Apr 2026
            </span>
          </div>

          {/* Price comparison grid */}
          <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, padding: 20, marginBottom: 16 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--foreground)', marginBottom: 14 }}>Perbandingan Harga</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
              {[
                { label: 'Harga Kamu /m²', val: fmtIDRShort(userPerSqm), sub: fmtIDRShort(hargaNum) + ' total', accent: vs.color },
                { label: 'Median Pasar /m²', val: fmtIDRShort(medianPerSqm), sub: fmtIDRShort(medianTotal) + ' total', accent: '#64748b' },
              ].map(({ label, val, sub, accent }) => (
                <div key={label} style={{ background: 'var(--muted)', borderRadius: 10, padding: '14px 12px' }}>
                  <div style={{ fontSize: 10, color: 'var(--muted-foreground)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>{label}</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: accent, fontFamily: 'var(--font-mono)', letterSpacing: '-0.02em', marginBottom: 3 }}>{val}</div>
                  <div style={{ fontSize: 11, color: 'var(--muted-foreground)', fontFamily: 'var(--font-mono)' }}>{sub}</div>
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              {[
                { label: 'Luas', val: luasNum + ' m²' },
                { label: 'Jenis', val: pt.charAt(0).toUpperCase() + pt.slice(1) },
                { label: 'Selisih /m²', val: (diffPct > 0 ? '+' : '') + diffPct + '%', color: diffPct > 15 ? '#dc2626' : diffPct < -15 ? '#2563eb' : '#16a34a' },
              ].map(({ label, val, color }) => (
                <div key={label} style={{ flex: 1, background: 'var(--muted)', borderRadius: 8, padding: '8px 10px', textAlign: 'center' }}>
                  <div style={{ fontSize: 10, color: 'var(--muted-foreground)', marginBottom: 2, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: color || 'var(--foreground)', fontFamily: 'var(--font-mono)' }}>{val}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Premium gate */}
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--foreground)', marginBottom: 10 }}>Kenapa harganya bisa begini?</div>
            {['Rentang harga P25–P75 di area ini','Riwayat transaksi 24 bulan terakhir','Perbandingan NJOP vs. harga pasar'].map(label => (
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
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--foreground)', marginBottom: 8 }}>Lihat rentang harga P25–P75 di area ini</div>
              <div style={{ display: 'inline-block', padding: '8px 16px', borderRadius: 8, background: accentColor, fontSize: 13, fontWeight: 600, color: '#fff' }}>
                Buka dengan Pro — Rp 49.000/bulan
              </div>
              <div style={{ fontSize: 11, color: 'var(--muted-foreground)', marginTop: 6 }}>Batalkan kapan saja · Tanpa kontrak</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10 }}>
            <button onClick={() => { setStage('IDLE'); setResult(null); }} style={{ flex: 1, padding: '12px', borderRadius: 8, border: '1.5px solid var(--border)', background: 'var(--card)', color: 'var(--foreground)', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>← Cek lagi</button>
            <button style={{ padding: '12px 16px', borderRadius: 8, border: `1.5px solid ${accentColor}`, background: '#fafaf9', color: accentColor, fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>📤 Bagikan</button>
          </div>

          <button onClick={() => onNavigate('wajar-gaji')} style={{ display: 'block', width: '100%', marginTop: 14, padding: '12px 16px', border: '1px solid var(--border)', borderRadius: 10, background: 'var(--muted)', cursor: 'pointer', textAlign: 'left', fontSize: 13 }}>
            💡 Cek juga standar gaji di {c} →{' '}<span style={{ color: '#3b82f6', fontWeight: 600 }}>Wajar Gaji</span>
          </button>
        </div>
      </div>
    );
  }

  // IDLE — form
  return (
    <div data-tool="wajar-tanah" style={{ minHeight: '80vh', background: bg, padding: '32px 0' }}>
      <div style={{ maxWidth: 560, margin: '0 auto', padding: '0 20px' }}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ fontSize: 40, marginBottom: 10 }}>🏡</div>
          <h1 style={{ fontSize: 'clamp(1.4rem, 3vw, 1.8rem)', fontWeight: 800, color: 'var(--foreground)', marginBottom: 6 }}>Cek Wajar Tanah</h1>
          <p style={{ fontSize: 13, color: 'var(--muted-foreground)' }}>Bandingkan harga properti dengan median pasar berdasarkan data BPN</p>
        </div>

        <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 14, padding: '24px', marginBottom: 12 }}>
          {/* Part 1 — Lokasi */}
          <div style={{ fontSize: 12, fontWeight: 700, color: accentColor, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>Lokasi Properti</div>

          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 6 }}>Provinsi</label>
            <FocusSelect value={province} onChange={p => { setProvince(p); setCity(''); setKecamatan(''); }} options={PROVINCES} placeholder="Pilih provinsi..." />
            {errors.province && <div style={{ fontSize: 11, color: '#dc2626', marginTop: 4 }}>{errors.province}</div>}
          </div>

          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 6 }}>
              Kota / Kabupaten
              {!province && <span style={{ fontSize: 11, color: 'var(--muted-foreground)', fontWeight: 400, marginLeft: 6 }}>— pilih provinsi dulu</span>}
            </label>
            <FocusSelect value={city} onChange={c => { setCity(c); setKecamatan(''); }} options={cities} placeholder="Pilih kota..." disabled={!province} />
            {errors.city && <div style={{ fontSize: 11, color: '#dc2626', marginTop: 4 }}>{errors.city}</div>}
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 6 }}>
              Kecamatan
              {!city && <span style={{ fontSize: 11, color: 'var(--muted-foreground)', fontWeight: 400, marginLeft: 6 }}>— pilih kota dulu</span>}
              <span style={{ fontSize: 11, color: 'var(--muted-foreground)', fontWeight: 400, marginLeft: 6 }}>(opsional)</span>
            </label>
            <FocusSelect value={kecamatan} onChange={setKecamatan} options={kecs} placeholder="Pilih kecamatan..." disabled={!city} />
          </div>

          <div style={{ borderTop: '1px solid var(--border)', margin: '0 0 16px' }} />

          {/* Part 2 — Properti */}
          <div style={{ fontSize: 12, fontWeight: 700, color: accentColor, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 12 }}>Detail Properti</div>

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 8 }}>Jenis Properti</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
              {PROP_TYPES.map(({ id, label, icon }) => (
                <button key={id} onClick={() => setPropType(id)} style={{
                  padding: '10px 4px', borderRadius: 10, border: '1.5px solid',
                  borderColor: propType === id ? accentColor : 'var(--border)',
                  background: propType === id ? '#f5f5f4' : 'var(--card)',
                  cursor: 'pointer', textAlign: 'center', transition: 'all 150ms',
                }}>
                  <div style={{ fontSize: 20, marginBottom: 4 }}>{icon}</div>
                  <div style={{ fontSize: 11, fontWeight: propType === id ? 700 : 500, color: propType === id ? accentColor : 'var(--muted-foreground)' }}>{label}</div>
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 }}>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 6 }}>Luas (m²)</label>
              <FocusInput value={luas} onChange={e => setLuas(e.target.value.replace(/\D/g,''))} placeholder="cth. 120" type="text" />
              {errors.luas && <div style={{ fontSize: 11, color: '#dc2626', marginTop: 4 }}>{errors.luas}</div>}
            </div>
            <div>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--foreground)', marginBottom: 6 }}>Harga Ditawarkan</label>
              <FocusInput {...{
                value: harga,
                onChange: e => { const r = e.target.value.replace(/\D/g,''); setHarga(r ? parseInt(r,10).toLocaleString('id-ID') : ''); },
                placeholder: 'cth. 800.000.000',
              }} />
              {errors.harga && <div style={{ fontSize: 11, color: '#dc2626', marginTop: 4 }}>{errors.harga}</div>}
            </div>
          </div>

          {/* Live price/m² calculation */}
          {pricePerSqm && (
            <div style={{ padding: '10px 14px', borderRadius: 8, background: '#f5f5f4', border: '1px solid #e7e5e4', marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>= harga per m²</span>
              <span style={{ fontSize: 15, fontWeight: 800, color: accentColor, fontFamily: 'var(--font-mono)' }}>{fmtIDRShort(pricePerSqm)}</span>
            </div>
          )}

          <button onClick={handleSubmit} style={{ width: '100%', padding: '14px', borderRadius: 10, border: 'none', background: accentColor, color: '#fff', fontSize: 15, fontWeight: 700, cursor: 'pointer' }}>
            Cek Harga Tanah →
          </button>
        </div>

        <div style={{ textAlign: 'center', fontSize: 12, color: 'var(--muted-foreground)' }}>Data dari BPN, notaris, dan listing publik.</div>
      </div>
    </div>
  );
}




// ─── kabur ───

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

/* fmtIDR stripped */

/* ResultSkeleton stripped */

/* const inputStyle stripped */

function FocusInputKabur({ value, onChange, placeholder, style }) {
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
            <FocusInputKabur placeholder="cth. 18.000.000" {...{
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
            <FocusInputKabur value={offerSalary} onChange={e => { const r = e.target.value.replace(/\D/g,''); setOfferSalary(r ? parseInt(r,10).toLocaleString('id-ID') : ''); }} placeholder={selectedCountry ? `cth. 5.000 ${selectedCountry.currency}` : 'Pilih negara dulu'} style={{ opacity: !country ? 0.5 : 1 }} />
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




// ─── hidup ───

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

/* fmtIDR stripped */

/* const inputStyle stripped */

/* ResultSkeleton stripped */

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




// ─── pages ───

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

/* fmtIDRShort stripped */

/* const inputStyle stripped */

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


