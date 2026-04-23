# cekwajar.id — UI/UX Enhancement Design Spec
## Version 1.0 | Target: "Best of the Best" | April 2026

---

## 1. Visual System — The Foundation

### 1.1 Color Palette

A professional financial tool needs a **trustworthy yet approachable** palette. Emerald conveys growth/money without the coldness of blue. Purple signals premium without feeling corporate.

```css
:root {
  /* Primary — Emerald: Trust, growth, Indonesian "Hijau" cultural resonance */
  --emerald-50:  #ecfdf5;
  --emerald-100: #d1fae5;
  --emerald-200: #a7f3d0;
  --emerald-300: #6ee7b7;
  --emerald-400: #34d399;
  --emerald-500: #10b981;
  --emerald-600: #059669;   /* PRIMARY */
  --emerald-700: #047857;
  --emerald-800: #065f46;
  --emerald-900: #064e3b;

  /* Accent — Amber: Highlights, warnings, premium badges */
  --amber-50:    #fffbeb;
  --amber-100:   #fef3c7;
  --amber-200:  #fde68a;
  --amber-400:  #fbbf24;
  --amber-500:  #f59e0b;   /* ACCENT */
  --amber-600:  #d97706;

  /* Neutrals — Slate: Text hierarchy, backgrounds */
  --slate-50:   #f8fafc;
  --slate-100:  #f1f5f9;
  --slate-200:  #e2e8f0;
  --slate-300:  #cbd5e1;
  --slate-400:  #94a3b8;
  --slate-500:  #64748b;
  --slate-600:  #475569;
  --slate-700:  #334155;
  --slate-800:  #1e293b;
  --slate-900:  #0f172a;

  /* Semantic */
  --success:    var(--emerald-600);
  --warning:    var(--amber-500);
  --error:      #ef4444;
  --premium:    #8b5cf6;    /* Purple for premium/pro */

  /* Surfaces */
  --background: var(--slate-50);
  --surface:    #ffffff;
  --surface-raised: #ffffff;

  /* Text */
  --text-primary:   var(--slate-900);
  --text-secondary: var(--slate-600);
  --text-muted:    var(--slate-400);
  --text-inverse:  #ffffff;

  /* Borders */
  --border:        var(--slate-200);
  --border-strong: var(--slate-300);
  --border-focus:  var(--emerald-500);
}
```

### 1.2 Typography

```css
:root {
  --font-display: 'Geist Sans', system-ui, sans-serif;
  --font-body:    'Geist Sans', system-ui, sans-serif;
  --font-mono:    'Geist Mono', ui-monospace, monospace;

  /* Scale */
  --text-xs:   0.75rem;    /* 12px — Badges, labels */
  --text-sm:   0.875rem;   /* 14px — Captions, hints */
  --text-base: 1rem;       /* 16px — Body */
  --text-lg:   1.125rem;   /* 18px — Large body */
  --text-xl:   1.25rem;    /* 20px — Card titles */
  --text-2xl:  1.5rem;     /* 24px — Section headers */
  --text-3xl:  1.875rem;   /* 30px — Page titles */
  --text-4xl:  2.25rem;    /* 36px — Hero sub */
  --text-5xl:  3rem;       /* 48px — Hero main */

  /* Line heights */
  --leading-tight:  1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.75;
}
```

### 1.3 Number Formatting (Critical for Financial App)

Indonesian users expect:
```
Rp 2.500.000     — Formal currency display
Rp 2,5jt         — Casual abbreviation (results, comparisons)
Rp 2.500.000,00  — Exact decimal (inputs, calculations)
12,5%            — Percentage with comma decimal
P50, P75, P25     — Percentile notation
```

### 1.4 Shadow System

```css
:root {
  --shadow-xs:  0 1px 2px rgba(0,0,0,0.04);
  --shadow-sm:  0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md:  0 4px 6px rgba(0,0,0,0.05), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg:  0 10px 15px rgba(0,0,0,0.06), 0 4px 6px rgba(0,0,0,0.04);
  --shadow-xl:  0 20px 25px rgba(0,0,0,0.08), 0 10px 10px rgba(0,0,0,0.04);
  --shadow-glow: 0 0 20px rgba(5, 150, 105, 0.15);  /* Emerald glow for success */
}
```

### 1.5 Border Radius

```css
:root {
  --radius-sm:  6px;   /* Buttons, inputs */
  --radius-md:  8px;   /* Cards */
  --radius-lg:  12px;  /* Modals, sheets */
  --radius-xl:  16px;  /* Large containers */
  --radius-full: 9999px; /* Pills, avatars */
}
```

### 1.6 Motion System

```css
:root {
  /* Durations */
  --duration-instant: 75ms;
  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 400ms;
  --duration-slower: 600ms;
  --duration-count: 1200ms; /* Number counting animation */

  /* Easings */
  --ease-out:     cubic-bezier(0, 0, 0.2, 1);   /* Enter */
  --ease-in:      cubic-bezier(0.4, 0, 1, 1);   /* Exit */
  --ease-in-out:  cubic-bezier(0.4, 0, 0.2, 1); /* State change */
  --ease-spring:  cubic-bezier(0.34, 1.56, 0.64, 1); /* Celebration */
  --ease-bounce:  cubic-bezier(0.68, -0.55, 0.265, 1.55); /* Playful */
}

/* Animation Keyframes */
@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes fadeInDown {
  from { opacity: 0; transform: translateY(-12px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes slideInRight {
  from { opacity: 0; transform: translateX(20px); }
  to   { opacity: 1; transform: translateX(0); }
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.95); }
  to   { opacity: 1; transform: scale(1); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.5; }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

@keyframes countUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes checkmark {
  0%   { stroke-dashoffset: 24; }
  100% { stroke-dashoffset: 0; }
}

@keyframes confetti {
  0%   { transform: translateY(0) rotate(0deg); opacity: 1; }
  100% { transform: translateY(-100px) rotate(720deg); opacity: 0; }
}

/* Utility classes */
.animate-fade-in        { animation: fadeIn var(--duration-normal) var(--ease-out); }
.animate-fade-in-up     { animation: fadeInUp var(--duration-slow) var(--ease-out); }
.animate-fade-in-down   { animation: fadeInDown var(--duration-slow) var(--ease-out); }
.animate-slide-in-right { animation: slideInRight var(--duration-slow) var(--ease-out); }
.animate-scale-in       { animation: scaleIn var(--duration-normal) var(--ease-out); }
.animate-pulse          { animation: pulse 2s var(--ease-in-out) infinite; }
.animate-spin           { animation: spin 1s linear infinite; }
.animate-shimmer        { animation: shimmer 1.5s infinite; }
```

---

## 2. Component Library Enhancements

### 2.1 Button Component

**States:**
- Default: Emerald background, white text
- Hover: Darker emerald, subtle scale(1.02), shadow lift
- Active/Pressed: Even darker, scale(0.98), no shadow
- Loading: Spinner replaces text, disabled state, loading-XXX color variant
- Disabled: 50% opacity, cursor-not-allowed

**Variants:**
```tsx
// Primary — Main CTAs
<Button variant="primary" size="lg">
  Cek Slip Gaji
</Button>

// Secondary — Alternative actions
<Button variant="secondary" size="lg">
  Lihat Semua
</Button>

// Ghost — Subtle actions
<Button variant="ghost">
  Batal
</Button>

// Outline — Borders without fill
<Button variant="outline">
  Masuk
</Button>

// Premium — Purple for upgrade CTAs
<Button variant="premium">
  Upgrade ke Pro
</Button>
```

**Animation specs:**
```css
.btn {
  transition: all var(--duration-fast) var(--ease-out);
}
.btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}
.btn:active:not(:disabled) {
  transform: translateY(0) scale(0.98);
  box-shadow: var(--shadow-xs);
}
```

### 2.2 Card Component

**Hover lift effect:**
```css
.card {
  transition: all var(--duration-normal) var(--ease-out);
  border: 1px solid var(--border);
}
.card:hover {
  border-color: var(--emerald-200);
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}
```

**Skeleton loading state:**
```tsx
<Card className="animate-pulse">
  <CardHeader className="space-y-3">
    <Skeleton className="h-5 w-1/3" />
    <Skeleton className="h-4 w-2/3" />
  </CardHeader>
  <CardContent>
    <Skeleton className="h-20 w-full" />
  </CardContent>
</Card>
```

### 2.3 Input Component

**Real-time formatting for IDR:**
```tsx
// As user types "2500000" → displays "Rp 2.500.000"
// On blur: formats to currency
// On focus: shows raw number for easy editing
```

**States:**
- Default: Gray border
- Focus: Emerald border, subtle glow
- Error: Red border, error message below
- Success: Green checkmark icon
- Disabled: Gray background

**Animation:**
```css
.input {
  transition: all var(--duration-fast) var(--ease-out);
}
.input:focus {
  border-color: var(--emerald-500);
  box-shadow: 0 0 0 3px var(--emerald-100);
  outline: none;
}
```

### 2.4 Badge Component

```tsx
// Verdict badges with semantic colors
<Badge variant="success">Sesuai Regulasi</Badge>    // Emerald
<Badge variant="error">Ada Pelanggaran</Badge>     // Red
<Badge variant="warning">Perhatian</Badge>         // Amber
<Badge variant="premium">Pro</Badge>               // Purple
<Badge variant="info">Basic</Badge>                 // Blue

// With animation on appear
<Badge className="animate-scale-in">Baru</Badge>
```

### 2.5 Toast/Notification Component

```tsx
// Success toast
<Toast variant="success">
  <CheckCircle className="h-5 w-5" />
  <div>
    <p className="font-medium">Audit berhasil!</p>
    <p className="text-sm opacity-80">3 pelanggaran ditemukan</p>
  </div>
</Toast>

// Enter from top-right, slide out after 5s
// Stack up to 3 toasts
// Click to dismiss
```

### 2.6 Progress/Stepper Component

For multi-step flows like wizard onboarding:
```tsx
<Stepper currentStep={2}>
  <Step label="Isi Data" />
  <Step label="Verifikasi" />
  <Step label="Hasil" />
</Stepper>

// Active step: emerald circle, bold label
// Completed step: checkmark, green
// Upcoming step: gray circle, muted label
// Connecting lines animate fill as progress
```

### 2.7 Loading Skeleton Component

```tsx
// Shimmer effect for loading states
<Skeleton className="h-4 w-full animate-shimmer" />
<Skeleton className="h-4 w-3/4" />
<Skeleton className="h-4 w-1/2" />

// Card skeleton for results
<Card className="animate-pulse">
  <CardContent className="space-y-4">
    <Skeleton className="h-8 w-32" />  {/* Verdict title */}
    <Skeleton className="h-4 w-full" />
    <Skeleton className="h-4 w-full" />
    <Skeleton className="h-4 w-2/3" />
  </CardContent>
</Card>
```

### 2.8 Number Ticker Component

For animated number displays in results:
```tsx
// Counts up from 0 to target value
<NumberTicker
  value={2500000}
  prefix="Rp "
  suffix=""
  duration={1200}
  locale="id-ID"
/>

// Triggers on mount and when value changes
// Each digit animates independently for satisfying effect
```

---

## 3. Page-Specific Enhancements

### 3.1 Homepage — First Impression

**Hero Section:**
```tsx
// Gradient background with subtle animation
<section className="bg-gradient-to-br from-emerald-50 via-white to-emerald-50/50">

// Large display typography
<h1 className="text-5xl font-bold tracking-tight">
  Audit Slip Gaji, Benchmark Gaji
  <span className="text-emerald-600"> & Harga Properti</span>
</h1>

// Animated arrow or icon in hero
// Staggered entrance animation (title → subtitle → CTA)
```

**Trust signals:**
```tsx
// Add below hero CTA
<div className="flex items-center justify-center gap-8 mt-8 text-sm text-slate-500">
  <div className="flex items-center gap-2">
    <Shield className="h-4 w-4 text-emerald-500" />
    <span>Data dienkripsi</span>
  </div>
  <div className="flex items-center gap-2">
    <Users className="h-4 w-4 text-emerald-500" />
    <span>12.000+ pengguna</span>
  </div>
  <div className="flex items-center gap-2">
    <Star className="h-4 w-4 text-amber-400" />
    <span>4.9 rating</span>
  </div>
</div>
```

**Tool Cards Grid:**
```tsx
// Better hover state
const ToolCard = ({ tool }) => (
  <Card className="group cursor-pointer overflow-hidden">
    {/* Colored top border on hover */}
    <div className="h-1 bg-gradient-to-r from-emerald-400 to-emerald-600 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300" />

    <CardContent className="p-6">
      {/* Icon with background */}
      <div className={`w-12 h-12 rounded-xl bg-${tool.color}-100 flex items-center justify-center mb-4`}>
        <tool.icon className={`h-6 w-6 text-${tool.color}-600`} />
      </div>

      <h3 className="font-semibold text-lg mb-2">{tool.name}</h3>
      <p className="text-slate-500 text-sm mb-4">{tool.description}</p>

      {/* Animated arrow */}
      <div className="flex items-center text-emerald-600 font-medium">
        <span>Mulai</span>
        <ArrowRight className="h-4 w-4 ml-1 transform group-hover:translate-x-1 transition-transform" />
      </div>
    </CardContent>
  </Card>
)
```

**Social Proof Section:**
```tsx
// Testimonials or usage stats
<section className="bg-slate-900 text-white py-16">
  <div className="max-w-5xl mx-auto text-center">
    <h2 className="text-3xl font-bold mb-8">Dipercaya oleh karyawan Indonesia</h2>
    <div className="grid grid-cols-3 gap-8">
      <div className="text-center">
        <div className="text-5xl font-bold text-emerald-400 mb-2">12.847</div>
        <div className="text-slate-400">Slip Gaji Di Audit</div>
      </div>
      <div className="text-center">
        <div className="text-5xl font-bold text-emerald-400 mb-2">Rp 2.1M</div>
        <div className="text-slate-400">Pelanggaran Ditemukan</div>
      </div>
      <div className="text-center">
        <div className="text-5xl font-bold text-emerald-400 mb-2">4.9</div>
        <div className="text-slate-400">Rating Pengguna</div>
      </div>
    </div>
  </div>
</section>
```

### 3.2 Wajar Slip — Core Audit Flow

**IDLE/Upload State:**
```tsx
// Better visual hierarchy
<div className="text-center space-y-6">
  {/* Large icon */}
  <div className="w-20 h-20 mx-auto bg-emerald-100 rounded-2xl flex items-center justify-center">
    <Receipt className="h-10 w-10 text-emerald-600" />
  </div>

  {/* Upload zone with dashed border */}
  <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 hover:border-emerald-400 hover:bg-emerald-50/50 transition-all cursor-pointer">
    <Upload className="h-8 w-8 mx-auto text-slate-400 mb-4" />
    <p className="font-medium">Drag slip gaji kamu di sini</p>
    <p className="text-sm text-slate-400">atau klik untuk pilih file</p>
  </div>
</div>

// Animated transition to processing
```

**OCR Processing State:**
```tsx
// Animated progress indicator
<div className="text-center space-y-4 py-12">
  <div className="relative w-24 h-24 mx-auto">
    <svg className="w-24 h-24 transform -rotate-90">
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
        className="text-slate-200"
      />
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="2"
        fill="none"
        strokeDasharray={31.4 * progress}
        className="text-emerald-500 transition-all duration-300"
      />
    </svg>
    <span className="absolute inset-0 flex items-center justify-center text-lg font-bold">
      {progress}%
    </span>
  </div>

  <p className="font-medium">Menganalisis slip gaji...</p>
  <p className="text-sm text-slate-500">
    {source === 'vision' ? 'Google Vision AI' : 'Tesseract OCR'}
  </p>
</div>
```

**Manual Form:**
```tsx
// Grouped form sections with visual separation
<div className="space-y-8">
  {/* Section 1: Income */}
  <FormSection title="Pendapatan" icon={DollarSign}>
    <FormField label="Gaji Bruto" hint="Gaji sebelum potong">
      <IDRInput {...register('grossSalary')} />
    </FormField>
  </FormSection>

  {/* Section 2: Deductions */}
  <FormSection title="Potongan" icon={MinusCircle}>
    {/* Deduction inputs */}
  </FormSection>

  {/* Section 3: Location */}
  <FormSection title="Lokasi" icon={MapPin}>
    {/* City, province selectors */}
  </FormSection>
</div>

// Animated section reveals
```

**IDR Input Component (Critical):**
```tsx
// Real-time formatting as user types
const IDRInput = ({ value, onChange }) => {
  const [displayValue, setDisplayValue] = useState('')

  // Format on blur
  const handleBlur = () => {
    const num = parseInt(value.replace(/\D/g, ''), 10)
    setDisplayValue(num.toLocaleString('id-ID'))
  }

  // Show raw on focus
  const handleFocus = () => {
    setDisplayValue(value)
  }

  // Format as typing
  const handleChange = (e) => {
    const raw = e.target.value.replace(/\D/g, '')
    onChange(raw)
    setDisplayValue(raw ? parseInt(raw).toLocaleString('id-ID') : '')
  }

  return (
    <div className="relative">
      <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">Rp</span>
      <Input
        value={displayValue}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        className="pl-8 font-mono"
      />
    </div>
  )
}
```

**Verdict Results (Most Important):**
```tsx
// Large verdict header with animation
<div className={`rounded-2xl p-8 text-center ${
  verdict === 'SESUAI' ? 'bg-emerald-50' : 'bg-red-50'
}`}>
  {/* Animated icon */}
  <div className="relative w-24 h-24 mx-auto mb-4">
    {verdict === 'SESUAI' ? (
      <CheckCircle className="w-24 h-24 text-emerald-500 animate-scale-in" />
    ) : (
      <AlertTriangle className="w-24 h-24 text-red-500 animate-scale-in" />
    )}
  </div>

  {/* Animated verdict text */}
  <h2 className="text-3xl font-bold mb-2 animate-fade-in-up">
    {verdict === 'SESUAI' ? 'Slip Gaji Sesuai!' : 'Ada Pelanggaran'}
  </h2>

  {/* Animated violation count */}
  <p className="text-lg text-slate-600 animate-fade-in-up" style={{animationDelay: '200ms'}}>
    {violationCount > 0
      ? `${violationCount} pelanggaran ditemukan pada slip gaji kamu`
      : 'Tidak ada pelanggaran ditemukan'}
  </p>
</div>

// Violation list with staggered animation
<div className="space-y-3 mt-6">
  {violations.map((v, i) => (
    <ViolationCard
      key={v.code}
      violation={v}
      style={{ animationDelay: `${(i + 1) * 100}ms` }}
      className="animate-fade-in-up"
    />
  ))}
</div>

// Calculations table with number ticker
<Table>
  <tbody>
    {calculations.map((row, i) => (
      <tr key={row.label} className="animate-fade-in" style={{animationDelay: `${i * 50}ms`}}>
        <td className="font-medium">{row.label}</td>
        <td className="text-right">
          <NumberTicker value={row.slip} prefix="Rp " />
        </td>
        <td className="text-right text-emerald-600 font-semibold">
          <NumberTicker value={row.correct} prefix="Rp " />
        </td>
      </tr>
    ))}
  </tbody>
</Table>
```

**Violation Card Animation:**
```tsx
const ViolationCard = ({ violation, ...props }) => (
  <Card
    className="border-l-4 border-l-red-500 animate-fade-in-up"
    style={props.style}
  >
    <CardContent className="p-4">
      <div className="flex items-start gap-4">
        {/* Animated icon */}
        <div className="w-10 h-10 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
          <AlertCircle className="w-5 h-5 text-red-600" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold">{violation.title}</span>
            <Badge variant="error" className="text-xs">{violation.code}</Badge>
          </div>
          <p className="text-sm text-slate-500 mt-1">{violation.description}</p>

          {/* Animated amount */}
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-sm text-slate-400">Selisih:</span>
            <span className="text-lg font-bold text-red-600">
              <NumberTicker
                value={violation.differenceIDR}
                prefix="Rp "
                duration={800}
              />
            </span>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
)
```

### 3.3 Wajar Tanah — Property Benchmark

**Form with Cascading Animation:**
```tsx
// Province/City/District selectors with smooth transitions
<div className="space-y-4">
  <Select
    value={province}
    onValueChange={handleProvinceChange}
    animation={true}  // Opens with fade + slide
  >
    {/* Options */}
  </Select>

  {/* City fades in when province selected */}
  <Select
    value={city}
    onValueChange={handleCityChange}
    disabled={!province}
    className={province ? 'animate-fade-in' : ''}
  >
    {/* Options */}
  </Select>
</div>

// Property type selector with visual cards
<div className="grid grid-cols-4 gap-3">
  {PROPERTY_TYPES.map(type => (
    <button
      key={type.value}
      onClick={() => setPropertyType(type.value)}
      className={`p-4 rounded-xl border-2 text-center transition-all ${
        propertyType === type.value
          ? 'border-emerald-500 bg-emerald-50'
          : 'border-slate-200 hover:border-slate-300'
      }`}
    >
      <type.icon className={`h-8 w-8 mx-auto mb-2 ${
        propertyType === type.value ? 'text-emerald-600' : 'text-slate-400'
      }`} />
      <span className="text-sm font-medium">{type.label}</span>
    </button>
  ))}
</div>
```

**Result Display:**
```tsx
// Verdict badge with dramatic reveal
<div className="text-center py-8">
  <div className="inline-block animate-scale-in">
    <VerdictBadge verdict={verdict} />
  </div>
</div>

// Price comparison cards with flip animation
<div className="grid grid-cols-2 gap-4 my-8">
  <Card className="text-center p-6 animate-fade-in-up">
    <div className="text-sm text-slate-500 mb-2">Harga Kamu</div>
    <div className="text-2xl font-bold">
      <NumberTicker value={askingPricePerSqm} prefix="Rp " suffix="/m²" />
    </div>
  </Card>

  <Card className="text-center p-6 bg-emerald-50 border-emerald-200 animate-fade-in-up" style={{animationDelay: '100ms'}}>
    <div className="text-sm text-slate-500 mb-2">Median Pasar</div>
    <div className="text-2xl font-bold text-emerald-700">
      <NumberTicker value={benchmark.p50} prefix="Rp " suffix="/m²" />
    </div>
  </Card>
</div>

// Price bar visualization
<PropertyPriceBar
  userPrice={askingPricePerSqm}
  p25={benchmark.p25}
  p50={benchmark.p50}
  p75={benchmark.p75}
  className="animate-fade-in" style={{animationDelay: '200ms'}}
/>
```

### 3.4 Dashboard — User Hub

**Quick Stats Cards:**
```tsx
<div className="grid grid-cols-4 gap-4">
  <StatCard
    label="Audit Bulan Ini"
    value={monthlyAudits}
    trend={+12}
    icon={FileText}
    className="animate-fade-in-up"
  />
  <StatCard
    label="Pelanggaran Ditemukan"
    value={totalViolations}
    trend={-3}
    icon={AlertTriangle}
    className="animate-fade-in-up" style={{animationDelay: '50ms'}}
  />
  <StatCard
    label="Total Hemat"
    value={totalSaved}
    prefix="Rp "
    icon={TrendingDown}
    className="animate-fade-in-up" style={{animationDelay: '100ms'}}
  />
  <StatCard
    label="Tier"
    value={tier}
    icon={Sparkles}
    className="animate-fade-in-up" style={{animationDelay: '150ms'}}
  />
</div>
```

**Audit History Timeline:**
```tsx
// Timeline view instead of list
<div className="relative">
  {/* Vertical line */}
  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-200" />

  {audits.map((audit, i) => (
    <div key={audit.id} className="relative pl-10 pb-8 animate-fade-in-up" style={{animationDelay: `${i * 100}ms`}}>
      {/* Timeline dot */}
      <div className={`absolute left-2.5 w-3 h-3 rounded-full border-2 ${
        audit.status === 'clean' ? 'bg-emerald-500 border-emerald-500' : 'bg-red-500 border-red-500'
      }`} />

      {/* Card */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{audit.toolName}</p>
              <p className="text-sm text-slate-500">{audit.date}</p>
            </div>
            <Badge variant={audit.status === 'clean' ? 'success' : 'error'}>
              {audit.status === 'clean' ? 'Sesuai' : `${audit.violationCount} Pelanggaran`}
            </Badge>
          </div>
        </CardContent>
      </Card>
    </div>
  ))}
</div>
```

### 3.5 Login/Auth — First Touchpoint

**Clean, Trust-Building Design:**
```tsx
// Centered card with subtle background
<div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-emerald-50/30">
  <Card className="w-full max-w-md animate-scale-in">
    <CardContent className="p-8">
      {/* Logo */}
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-emerald-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <Calculator className="h-8 w-8 text-emerald-600" />
        </div>
        <h1 className="text-2xl font-bold">cekwajar.id</h1>
        <p className="text-slate-500 mt-1">Audit slip gaji jadi mudah</p>
      </div>

      {/* Google button with hover effect */}
      <Button
        variant="outline"
        className="w-full h-12 gap-3 hover:bg-slate-50 transition-colors"
      >
        <GoogleIcon className="h-5 w-5" />
        <span>Lanjutkan dengan Google</span>
      </Button>

      {/* Divider */}
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-slate-200" />
        </div>
        <div className="relative flex justify-center">
          <span className="bg-white px-4 text-sm text-slate-400">atau</span>
        </div>
      </div>

      {/* Magic link form */}
      <form className="space-y-4">
        <Input
          type="email"
          placeholder="email@perusahaan.com"
          className="h-12"
        />
        <Button className="w-full h-12">Kirim Link Masuk</Button>
      </form>

      {/* Trust signals */}
      <div className="mt-6 pt-6 border-t text-center">
        <p className="text-xs text-slate-400">
          Dengan masuk, kamu menyetujui{' '}
          <a href="/terms" className="underline hover:text-emerald-600">Syarat</a> dan{' '}
          <a href="/privacy" className="underline hover:text-emerald-600">Privasi</a> kami.
          Data kamu 100% aman.
        </p>
      </div>
    </CardContent>
  </Card>
</div>
```

### 3.6 Upgrade/Pricing — Conversion Pages

**Billing Toggle with Animation:**
```tsx
<div className="inline-flex bg-slate-100 rounded-xl p-1">
  <button
    onClick={() => setPeriod('monthly')}
    className={`px-6 py-2 rounded-lg text-sm font-medium transition-all ${
      period === 'monthly'
        ? 'bg-white shadow-sm text-slate-900'
        : 'text-slate-500 hover:text-slate-700'
    }`}
  >
    Bulanan
  </button>
  <button
    onClick={() => setPeriod('annual')}
    className={`px-6 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
      period === 'annual'
        ? 'bg-white shadow-sm text-slate-900'
        : 'text-slate-500 hover:text-slate-700'
    }`}
  >
    Tahunan
    <Badge variant="success" className="text-xs animate-bounce">HEMAT 20%</Badge>
  </button>
</div>
```

**Pricing Cards with Popular Highlight:**
```tsx
<Card className={`relative overflow-hidden transition-all duration-300 ${
  isPopular ? 'border-emerald-500 shadow-xl scale-105' : 'border-slate-200'
}`}>
  {isPopular && (
    <>
      {/* Glow effect */}
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-100/50 to-transparent" />
      <div className="absolute top-0 right-0 bg-emerald-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
        PALING POPULER
      </div>
    </>
  )}

  <CardContent className="relative">
    {/* Price with animated number */}
    <div className="text-4xl font-bold mb-1">
      <NumberTicker
        value={price}
        prefix="Rp "
        duration={600}
      />
    </div>

    {/* Features with checkmark animation */}
    <ul className="space-y-3 mt-6">
      {features.map((f, i) => (
        <li key={f.label} className="flex items-center gap-3 animate-fade-in" style={{animationDelay: `${i * 50}ms`}}>
          <CheckCircle className="h-5 w-5 text-emerald-500 flex-shrink-0" />
          <span>{f.label}</span>
        </li>
      ))}
    </ul>

    {/* CTA with hover animation */}
    <Button className="w-full mt-8 h-12 group">
      {label}
      <ArrowRight className="h-4 w-4 ml-2 group-hover:translate-x-1 transition-transform" />
    </Button>
  </CardContent>
</Card>
```

---

## 4. Micro-Interactions Library

### 4.1 Button Press Feedback
```css
.btn:active {
  transform: scale(0.97);
  transition-duration: 50ms;
}
```

### 4.2 Card Hover Lift
```css
.card-hover {
  transition: transform var(--duration-normal) var(--ease-out),
              box-shadow var(--duration-normal) var(--ease-out);
}
.card-hover:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-xl);
}
```

### 4.3 Input Focus Glow
```css
.input:focus {
  border-color: var(--emerald-500);
  box-shadow: 0 0 0 3px var(--emerald-100);
}
```

### 4.4 Checkbox/Toggle Animation
```css
.toggle {
  transition: background-color var(--duration-fast) var(--ease-out);
}
.toggle[data-state="checked"] {
  background-color: var(--emerald-500);
}
.toggle-thumb {
  transition: transform var(--duration-fast) var(--ease-spring);
}
.toggle[data-state="checked"] .toggle-thumb {
  transform: translateX(16px);
}
```

### 4.5 Skeleton Shimmer
```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--slate-200) 0%,
    var(--slate-100) 50%,
    var(--slate-200) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}
```

### 4.6 Toast Slide-In
```css
.toast-enter {
  animation: slideInRight var(--duration-slow) var(--ease-out);
}
.toast-exit {
  animation: slideOutRight var(--duration-normal) var(--ease-in);
}
@keyframes slideOutRight {
  to { opacity: 0; transform: translateX(100%); }
}
```

### 4.7 Number Ticker
```tsx
// Each digit animates independently for counting effect
const NumberTicker = ({ value, duration = 1200, ...props }) => {
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    const start = 0
    const end = value
    const startTime = performance.now()

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)

      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplay(Math.floor(start + (end - start) * eased))

      if (progress < 1) {
        requestAnimationFrame(animate)
      }
    }

    requestAnimationFrame(animate)
  }, [value, duration])

  return <span {...props}>{display.toLocaleString('id-ID')}</span>
}
```

### 4.8 Success Celebration (Subtle)
```tsx
// On audit complete, subtle confetti burst
const Confetti = ({ trigger }) => {
  if (!trigger) return null

  return (
    <div className="fixed inset-0 pointer-events-none z-50">
      {[...Array(20)].map((_, i) => (
        <div
          key={i}
          className="absolute w-2 h-2 rounded-full animate-confetti"
          style={{
            left: `${Math.random() * 100}%`,
            top: '50%',
            backgroundColor: ['#10b981', '#f59e0b', '#8b5cf6'][i % 3],
            animationDelay: `${Math.random() * 300}ms`,
            animationDuration: `${600 + Math.random() * 400}ms`,
          }}
        />
      ))}
    </div>
  )
}
```

### 4.9 Page Transition
```tsx
// Fade + slide between pages
<div className="page-transition-enter">
  {/* Content fades in, slight upward motion */}
</div>

<style>{`
  .page-transition-enter {
    animation: fadeInUp var(--duration-slow) var(--ease-out);
  }
`}</style>
```

---

## 5. Animation Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Implement CSS variables for colors, spacing, shadows
- [ ] Implement motion tokens and keyframes
- [ ] Create NumberTicker component
- [ ] Create Skeleton component
- [ ] Create Toast component
- [ ] Upgrade Button with all variants and states
- [ ] Upgrade Card with hover effects

### Phase 2: Forms (Week 2)
- [ ] Implement IDRInput with real-time formatting
- [ ] Add loading skeletons to all forms
- [ ] Implement form field animations (focus, error, success)
- [ ] Add staggered form section reveals

### Phase 3: Results (Week 3)
- [ ] Animate verdict cards on audit complete
- [ ] Implement NumberTicker in results
- [ ] Add violation card staggered animation
- [ ] Create subtle confetti for successful audits
- [ ] Animate calculation table rows

### Phase 4: Pages (Week 4)
- [ ] Add homepage hero animation
- [ ] Animate trust signals on scroll
- [ ] Add tool card hover effects
- [ ] Implement dashboard stat card animations
- [ ] Animate pricing toggle
- [ ] Add pricing card entrance animations

### Phase 5: Polish (Week 5)
- [ ] Implement page transitions
- [ ] Add loading skeletons to data fetching
- [ ] Implement skeleton for navigation
- [ ] Add skeleton for premium gates
- [ ] Final accessibility review (respect prefers-reduced-motion)

---

## 6. Accessibility

### Motion Preferences
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Focus Management
```tsx
// Always visible focus rings for keyboard navigation
*:focus-visible {
  outline: 2px solid var(--emerald-500);
  outline-offset: 2px;
}
```

### Screen Reader Announcements
```tsx
// Announce dynamic content changes
<div aria-live="polite" className="sr-only">
  {announcement}
</div>
```

---

## 7. Responsive Behavior

### Mobile (< 640px)
- Single column layouts
- Full-width buttons
- Bottom sheet for mobile menus
- Larger touch targets (min 44px)
- Simplified animations (no complex transitions)

### Tablet (640px - 1024px)
- 2-column grids
- Side navigation collapses to icons
- Touch-optimized hover states

### Desktop (> 1024px)
- Full animations enabled
- Multi-column layouts
- Hover states active
- Keyboard shortcuts

---

## 8. Performance

### Animation Performance
```css
/* Use transform/opacity only for animations */
.animated {
  will-change: transform, opacity;
  transform: translateZ(0); /* Force GPU */
}

/* Avoid animating layout properties */
```

### Code Splitting
```tsx
// Lazy load animation-heavy components
const ResultsAnimation = dynamic(() => import('./ResultsAnimation'), {
  loading: () => <Skeleton />
})
```

---

## 9. Testing Checklist

### Visual
- [ ] All animations smooth at 60fps
- [ ] No layout shift during load
- [ ] Consistent across browsers (Chrome, Safari, Firefox)
- [ ] Dark mode support (future)

### Functional
- [ ] Forms work without JS
- [ ] Loading states appear correctly
- [ ] Error states are clear
- [ ] Keyboard navigation works
- [ ] Screen reader announces changes

### Performance
- [ ] First Contentful Paint < 1.5s
- [ ] Largest Contentful Paint < 2.5s
- [ ] No janky animations
- [ ] Efficient re-renders

---

## Appendix: Component File Structure

```
src/
├── components/
│   ├── ui/
│   │   ├── button.tsx          # Enhanced with loading state
│   │   ├── card.tsx            # Enhanced with hover effects
│   │   ├── input.tsx           # Enhanced with formatting
│   │   ├── select.tsx          # Enhanced with animation
│   │   ├── badge.tsx           # Semantic color variants
│   │   ├── skeleton.tsx        # NEW: Loading placeholder
│   │   ├── toast.tsx           # NEW: Toast notification
│   │   └── number-ticker.tsx   # NEW: Animated number
│   ├── forms/
│   │   ├── idr-input.tsx       # NEW: Currency formatting
│   │   ├── form-section.tsx    # NEW: Animated section
│   │   └── index.ts
│   ├── feedback/
│   │   ├── loading-skeleton.tsx
│   │   ├── progress.tsx
│   │   └── confetti.tsx        # NEW: Celebration effect
│   └── index.ts
├── hooks/
│   ├── use-animated-value.ts   # NEW: Number animation
│   ├── use-reduced-motion.ts   # NEW: A11y check
│   └── index.ts
├── lib/
│   ├── animations.ts            # NEW: Animation utilities
│   └── formatters.ts           # IDR formatting
└── styles/
    └── globals.css             # Motion tokens, base styles
```

---

*Design spec created: 2026-04-16*
*Version: 1.0*
