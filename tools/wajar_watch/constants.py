"""WAJAR_WATCH constants — single source of truth. Never hardcode elsewhere."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# ── Verified repo & file references ─────────────────────────────────────────
CEKWAJAR_GITHUB_OWNER = "Bashara-aina"
CEKWAJAR_GITHUB_REPO = "slip_cekwajar_id"  # VERIFIED 2026-03-12
CEKWAJAR_BASE_BRANCH = "main"
CEKWAJAR_REGULATIONS_FILE = "lib/regulations.ts"  # VERIFIED 2026-03-12
CEKWAJAR_PPH21_FILE = "lib/pph21-ter.ts"  # VERIFIED 2026-03-12

# ── Supabase table names ──────────────────────────────────────────────────────
TABLE_REGULATION_CONSTANTS = "regulation_constants"
TABLE_PAGE_HASHES = "regulation_page_hashes"
TABLE_CHANGE_LOG = "regulation_change_log"
TABLE_PIPELINE_LOG = "pipeline_run_log"

# ── Regulation sources ────────────────────────────────────────────────────────
REGULATION_SOURCES = [
    {
        "id": "bpjstk_peraturan",
        "name": "BPJS Ketenagakerjaan — Peraturan",
        "url": "https://www.bpjsketenagakerjaan.go.id/peraturan.html",
        "keywords": ["jaminan pensiun", "batas upah", "iuran", "surat edaran"],
        "type": "html",
        "priority": "high",
    },
    {
        "id": "peraturan_go_id",
        "name": "peraturan.go.id",
        "url": "https://peraturan.go.id/search?q=jaminan+pensiun+BPJS",
        "keywords": ["jaminan pensiun", "batas upah", "PTKP", "tarif efektif"],
        "type": "html",
        "priority": "high",
    },
    {
        "id": "bpk_peraturan",
        "name": "BPK — Database Peraturan",
        "url": "https://peraturan.bpk.go.id/Search?q=jaminan+pensiun",
        "keywords": ["jaminan pensiun", "BPJS", "PP", "Perpres", "PMK"],
        "type": "html",
        "priority": "medium",
    },
    {
        "id": "pajak_go_id",
        "name": "DJP — pajak.go.id",
        "url": "https://www.pajak.go.id/id/peraturan",
        "keywords": ["tarif efektif rata-rata", "PPh 21", "PTKP", "PMK"],
        "type": "html",
        "priority": "medium",
    },
    {
        "id": "bps_berita_resmi",
        "name": "BPS — Berita Resmi Statistik",
        "url": "https://www.bps.go.id/id/pressrelease",
        "keywords": ["produk domestik bruto", "PDB", "pertumbuhan ekonomi"],
        "type": "html",
        "priority": "low",
        "notes": "PDB growth rate used to verify JP wage cap formula each Feb.",
    },
]

# ── WatchedConstant — one per numerical constant we track ────────────────────
@dataclass
class WatchedConstant:
    key: str
    description: str
    code_path: str  # dot-notation path inside regulations.ts
    current_value: float | int
    effective_date: str  # "YYYY-MM-DD"
    legal_basis: str
    legal_basis_url: str
    update_trigger: str  # "annual_february" | "rare" | "ad_hoc"
    change_type: str  # "cap" | "rate" | "bracket" | "fixed"
    auto_apply_allowed: bool  # ONLY True for caps. NEVER for rates.
    formula: Optional[str] = None
    sources_required: int = 2


WATCHED_CONSTANTS: list[WatchedConstant] = [
    # ── BPJS JP — wage cap (CAP = auto-apply eligible) ───────────────────────
    WatchedConstant(
        key="bpjs_jp_wage_cap_2026",
        description="BPJS JP batas upah 2026 (effective 1 March 2026)",
        code_path="BPJS_JP.wageCap2026",
        current_value=11_086_300,  # CORRECT per SE B/1226/022026
        effective_date="2026-03-01",
        legal_basis="SE BPJS Ketenagakerjaan B/1226/022026",
        legal_basis_url=(
            "https://494075.fs1.hubspotusercontent-na1.net/hubfs/494075/"
            "compliance-portal/notification-number-b1226022026.pdf"
        ),
        update_trigger="annual_february",
        change_type="cap",
        auto_apply_allowed=True,
        formula="prev_year_cap * (1 + pdb_growth_rate)",
        sources_required=2,
    ),
    WatchedConstant(
        key="bpjs_jp_wage_cap_2025",
        description="BPJS JP batas upah 2025 (effective 1 March 2025)",
        code_path="BPJS_JP.wageCap2025",
        current_value=10_547_400,
        effective_date="2025-03-01",
        legal_basis="SE BPJS Ketenagakerjaan 2025",
        legal_basis_url="https://www.bpjsketenagakerjaan.go.id/peraturan.html",
        update_trigger="annual_february",
        change_type="cap",
        auto_apply_allowed=True,
        formula="prev_year_cap * (1 + pdb_growth_rate)",
        sources_required=2,
    ),
    # ── BPJS JP — rate (RATE = NEVER auto-apply) ─────────────────────────────
    WatchedConstant(
        key="bpjs_jp_employee_rate",
        description="BPJS JP iuran karyawan (1% per PP 45/2015)",
        code_path="BPJS_JP.employeeRate",
        current_value=0.01,
        effective_date="2015-07-01",
        legal_basis="PP No. 45/2015 Pasal 6",
        legal_basis_url="https://peraturan.bpk.go.id/Details/5613/pp-no-45-tahun-2015",
        update_trigger="rare",
        change_type="rate",
        auto_apply_allowed=False,
        sources_required=3,
    ),
    WatchedConstant(
        key="bpjs_jp_employer_rate",
        description="BPJS JP iuran pemberi kerja (2% per PP 45/2015)",
        code_path="BPJS_JP.employerRate",
        current_value=0.02,
        effective_date="2015-07-01",
        legal_basis="PP No. 45/2015 Pasal 6",
        legal_basis_url="https://peraturan.bpk.go.id/Details/5613/pp-no-45-tahun-2015",
        update_trigger="rare",
        change_type="rate",
        auto_apply_allowed=False,
        sources_required=3,
    ),
    # ── BPJS Kesehatan ───────────────────────────────────────────────────────
    WatchedConstant(
        key="bpjs_kesehatan_employee_rate",
        description="BPJS Kesehatan iuran karyawan (1% per Perpres 64/2020)",
        code_path="BPJS_KESEHATAN.employeeRate",
        current_value=0.01,
        effective_date="2020-07-14",
        legal_basis="Perpres No. 64/2020",
        legal_basis_url="https://peraturan.bpk.go.id/Details/136650/perpres-no-64-tahun-2020",
        update_trigger="rare",
        change_type="rate",
        auto_apply_allowed=False,
        sources_required=3,
    ),
    WatchedConstant(
        key="bpjs_kesehatan_wage_cap",
        description="BPJS Kesehatan batas upah (Rp12.000.000)",
        code_path="BPJS_KESEHATAN.wageCap",
        current_value=12_000_000,
        effective_date="2020-07-14",
        legal_basis="Perpres No. 64/2020",
        legal_basis_url="https://peraturan.bpk.go.id/Details/136650/perpres-no-64-tahun-2020",
        update_trigger="rare",
        change_type="cap",
        auto_apply_allowed=True,
        sources_required=2,
    ),
    # ── BPJS JHT ─────────────────────────────────────────────────────────────
    WatchedConstant(
        key="bpjs_jht_employee_rate",
        description="BPJS JHT iuran karyawan (2% per PP 46/2015)",
        code_path="BPJS_JHT.employeeRate",
        current_value=0.02,
        effective_date="2015-07-01",
        legal_basis="PP No. 46/2015",
        legal_basis_url="https://peraturan.bpk.go.id/Details/5614/pp-no-46-tahun-2015",
        update_trigger="rare",
        change_type="rate",
        auto_apply_allowed=False,
        sources_required=3,
    ),
    # ── PTKP ─────────────────────────────────────────────────────────────────
    WatchedConstant(
        key="ptkp_tk0_annual",
        description="PTKP TK/0 tahunan (Rp54.000.000)",
        code_path="PTKP.TK0",
        current_value=54_000_000,
        effective_date="2016-01-01",
        legal_basis="PMK No. 101/PMK.010/2016",
        legal_basis_url="https://peraturan.bpk.go.id/Details/108843",
        update_trigger="rare",
        change_type="fixed",
        auto_apply_allowed=False,
        sources_required=3,
    ),
    # ── Pasal 17 bracket 1 ───────────────────────────────────────────────────
    WatchedConstant(
        key="pasal17_bracket1_rate",
        description="PPh Pasal 17 bracket 1: 5% s/d Rp60jt (UU HPP)",
        code_path="PASAL17[0].rate",
        current_value=0.05,
        effective_date="2022-01-01",
        legal_basis="UU No. 7/2021 (HPP) Pasal 17",
        legal_basis_url="https://peraturan.bpk.go.id/Details/182060",
        update_trigger="rare",
        change_type="bracket",
        auto_apply_allowed=False,
        sources_required=3,
    ),
]

# ── Confidence levels ─────────────────────────────────────────────────────────
CONFIDENCE_HIGH = "HIGH"
CONFIDENCE_MEDIUM = "MEDIUM"
CONFIDENCE_LOW = "LOW"
CONFIDENCE_BLOCK = "BLOCK"

# ── Routing decisions ─────────────────────────────────────────────────────────
ROUTE_AUTO_APPLY = "auto_apply"
ROUTE_ALERT_HUMAN = "alert_human"
ROUTE_ALERT_ONLY = "alert_only"
ROUTE_BLOCK = "block"
ROUTE_SKIP = "skip"

# ── Safety constants ──────────────────────────────────────────────────────────
NOISE_THRESHOLD = 0.001  # ignore changes < 0.1%
MAX_EXPECTED_CAP_DELTA = 0.15  # JP cap should never jump > 15% YoY
DECREASE_CAP_POLICY = "alert_human"

# ── HARDCODED BLOCKLIST — defense in depth ────────────────────────────────────
# Even if auto_apply_allowed=True is accidentally set on these keys,
# the pipeline MUST refuse auto-apply and escalate to BLOCK.
NEVER_AUTO_APPLY_KEYS = {
    "bpjs_jp_employee_rate",
    "bpjs_jp_employer_rate",
    "bpjs_kesehatan_employee_rate",
    "bpjs_jht_employee_rate",
    "ptkp_tk0_annual",
    "pasal17_bracket1_rate",
}

# ── Schedule ───────────────────────────────────────────────────────────────────
CRON_UTC = "0 23 * * *"  # 23:00 UTC = 06:00 WIB
HIGH_ALERT_MONTHS = [2, 3]  # February & March — JP cap season
