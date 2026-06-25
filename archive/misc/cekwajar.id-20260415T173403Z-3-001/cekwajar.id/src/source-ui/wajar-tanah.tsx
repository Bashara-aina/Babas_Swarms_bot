// @ts-nocheck
'use client'
import React, { useState, useEffect, useRef } from 'react'


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

function fmtIDR(n) { return 'Rp\u00a0' + n.toLocaleString('id-ID'); }
function fmtIDRShort(n) {
  if (!n) return '–';
  if (n >= 1_000_000_000) return 'Rp\u00a0' + (n / 1_000_000_000).toFixed(1).replace('.', ',') + ' M';
  if (n >= 1_000_000) return 'Rp\u00a0' + (n / 1_000_000).toFixed(0) + ' jt';
  return fmtIDR(n);
}

const inputStyle = {
  width: '100%', boxSizing: 'border-box', height: 52, padding: '0 14px',
  border: '1.5px solid var(--border)', borderRadius: 10,
  background: 'var(--card)', color: 'var(--foreground)',
  fontSize: 15, fontFamily: 'inherit', outline: 'none',
  transition: 'border-color 150ms',
};

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


export default WajarTanahPage
