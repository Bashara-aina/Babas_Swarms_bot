// @ts-nocheck
'use client'
import React, { useState, useEffect } from 'react'
import { WordmarkLogo } from '@/components/WordmarkLogo'


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
          display: 'flex', alignItems: 'center',
          background: 'none', border: 'none', cursor: 'pointer', padding: 0,
        }}>
          <WordmarkLogo size="md" />
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
              <div style={{ marginBottom: 8 }}>
                <WordmarkLogo size="sm" />
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


export { GlobalNav, SiteFooter }
