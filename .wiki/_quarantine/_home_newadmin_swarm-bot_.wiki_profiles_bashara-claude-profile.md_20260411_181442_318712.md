---
{
  "page_path": "/home/newadmin/swarm-bot/.wiki/profiles/bashara-claude-profile.md",
  "reason": "daily_fast_scan: score=0.200 < 0.3",
  "score": 0.2,
  "quarantined_at": "2026-04-11T18:14:42.318846"
}
---

# Bashara — Claude Profile Export

> Generated: April 2026 | Source: Conversation history + public profiles
> Links: [GitHub](https://github.com/Bashara-aina) · [LinkedIn](https://linkedin.com/in/bashara-aina) · [Medium](https://medium.com/@basharaaina) · [ResearchGate](https://www.researchgate.net/profile/Bashara-Aina) · [Rumah Labuh](https://rumahlabuh.com)

---

## 1. Identity & Context

* **Full name:** Bashara Aina
* **Nationality:** Indonesian
* **Current location:** Tokyo, Japan (Toyosu area, Shibaura Institute of Technology)
* **Academic status:** Master's student, Data Science / Deep Learning, SIT — expected graduation 2026–2027
* **Scholarship:** MEXT (Japanese government scholarship)
* **Previous institution:** Institut Teknologi Sepuluh Nopember (ITS), Surabaya
* **Came to Japan:** Initially as an exchange student in 2023, converted to regular master's student
* **Professional background:** Data analysis & Master Data Management at Danone Indonesia
* **Mentor:** Mauro Portela, Managing Director at Danone

---

## 2. Technical Skills & Stack

### Strong / Actively Used
* **Python** — primary language across all projects (ML, scripting, data pipelines)
* **PyTorch** — used for thesis deep learning work (ResNet-50, FPN, multi-task heads)
* **SQL** — MySQL, MS SQL Server; used at Danone and in data projects
* **Pandas / NumPy / Scikit-learn / Seaborn** — standard ML/analytics toolkit
* **Git / GitHub** — 25 public repos, uses it for research and portfolio

### Used in Projects
* **FastAPI** — backend for AquaCast forecasting system
* **Streamlit** — frontend for data dashboards
* **Next.js** — built the Rumah Labuh booking site
* **Supabase** — database/backend for Rumah Labuh
* **Midtrans** — Indonesian payment gateway integration
* **Fonnte** — WhatsApp API for automated notifications (boarding house system)
* **OpenCV** — listed in GitHub profile
* **MATLAB** — used for ECG/pulse oximeter data in Applied Neuroergonomics coursework
* **GCP (Google Cloud Platform)** — listed in GitHub tools
* **Figma / Adobe XD / Photoshop** — design tooling

### Knows / Has Used
* Java, PHP, JavaScript — in GitHub profile
* Power BI, Tableau — mentioned in GitHub bio
* Linux (Ubuntu 22.04) — thesis hardware environment
* Jupyter Notebooks — primary research/analysis environment

### Active Learning
* JLPT N2 Japanese (aggressive self-study goal, using Bunpro, JPDB, Renshuu)
* Deep Learning architecture design (thesis-level, not beginner)

---

## 3. Projects

### WorkerNet / POPW (Primary Thesis — Top Priority)
**Proof of Physical Work** — multi-task deep learning system for IKEA assembly action recognition.

* **Architecture:** ResNet-50 backbone + FPN, three heads: object detection (7 classes, RetinaNet-style), 2D pose estimation (17 COCO keypoints, soft-argmax), assembly action classification (33 actions)
* **Key module:** FiLM conditioning — activity features conditioned on pose output. C5 routes directly to FiLM (bypasses FPN). P3 feeds only pose head. P3–P7 feed detection.
* **Activity head input:** always `[B, 2304]` — concatenation of GAP(C5_mod) and GAP(P4)
* **FiLM scaling:** γ uses `1 + tanh ∈ (0, 2)`, β is linear and unbounded
* **Residual MLP:** 2304 → 512 → 256 → 512 + skip
* **Loss:** Kendall uncertainty-weighted multi-task loss; clamp widened to `[-4, 2]`
* **Hardware:** NVIDIA RTX 3060 12GB, Ubuntu 22.04, Python 3.13
* **Dataset:** IKEA ASM dataset
* **Confirmed bug fixes:** soft-argmax boundary bias, anchor ordering (ratios-outer/scales-inner), `log_var_pose` init at -1.0, `self.samples` population
* **Related work:** Conducted rigorous audit of 17 benchmark papers — found majority contained fabricated or misattributed metrics. Identified Ego-Exo4D and HA-ViD as strongest comparable datasets (triple annotation: activity + object + 2D keypoints)
* **GitHub:** `popw-protocol` repo (README preference: single file, simple)

### AquaCast (Portfolio Project)
Weather-driven demand forecasting for CPG beverage companies. Went through multiple iterations:
* **AquaCast Sentinel** — Indonesia-specific, modeled on Danone AQUA use case
* **AquaCast Global v1.1** — globally applicable, public-data-only
* Stack: Open-Meteo API + Corporación Favorita data + FastAPI + Streamlit
* Produced 8 technical spec documents, fact-checked 30+ claims rigorously

### Rumah Labuh / Labuh Banyu (Real Business)
Online booking system for two premium boarding house properties in Laweyan, Surakarta:
* **Labuh Biru:** 23 rooms, Jl. Joko Tingkir No.22
* **Labuh Banyu:** 9 rooms, Jl. Sidomukti Tim. No.33
* **Live site:** [rumahlabuh.com](https://rumahlabuh.com)
* **Tech stack:** Next.js, Supabase, Midtrans (payment), Fonnte (WhatsApp API)
* **Features designed:** adaptive pricing, branch-specific booking codes, digital contract signing, cash/manual booking support, 3-step booking flow

### Sate Taichan Gendhut
Restaurant business in Indonesia (operational, separate from boarding house).

### SIT Research (Earlier)
Comparative study pairing BERT and GPT models for sentiment analysis — done during SIT research program. Pinned on GitHub.

### Other Portfolio Projects (GitHub)
* **IDX Data Scientist internship** — credit risk prediction (ML end-to-end)
* **Accenture analytics project** — social media content strategy analytics
* **Kimia Farma big data** — sales optimization analytics
* **BTPN data engineering** — customer retention in credit card services
* **Hotel Pajang Indah** — operational analytics case study
* **LeetCode solved** — Python solutions, ongoing

### UNIQLO GMP Application (2026)
Applied for UNIQLO Global Management Program 2026. Positioned as a "Bridge Candidate" between Japan HQ and Southeast Asian markets.

### ADB-Japan Scholarship at Keio University
Explored this as a potential next academic step.

---

## 4. Coding Patterns & Preferences

* **File philosophy:** Prefers single-file solutions for READMEs and configs. Explicitly stated: "keep it simple in one file." For Python code, still wants comprehensive and clean.
* **Documentation style:** Minimal markdown for docs, full rigor for code.
* **Prototyping style:** Builds architecturally ambitious systems (multi-head, multi-loss) but is careful about implementation details — asks about specific tensor shapes, initialization values, loss clamping ranges.
* **Debugging approach:** Methodical — tracks bug fixes explicitly, names them (e.g., "soft-argmax boundary bias," "anchor ordering fix").
* **Hardware-aware:** Designs with a specific GPU constraint in mind (RTX 3060 12GB); thinks about memory footprint.
* **Prefers specificity:** When asking for code or architecture help, gives precise details and expects precise answers back.
* **Self-study documentation:** Creates NotebookLM prompts, SVG architecture diagrams, and benchmark audit tables — treats documentation as a learning tool.

---

## 5. Recurring Pain Points

* **Benchmark credibility in academic papers** — Had to audit 17 papers and found widespread fabricated/misattributed metrics. Deep frustration with this. Built a personal audit methodology.
* **Multi-task loss balancing** — Kendall uncertainty weighting, log_var initialization, and clamp ranges required multiple debugging sessions.
* **FiLM conditioning integration** — Routing C5 vs FPN features, ensuring dimensions match, residual MLP design — iterated through multiple times.
* **Japanese job applications** — Repeatedly needed help with Japanese interview prep, CV formatting, application emails (Italian restaurant, gluten-free restaurant, game QA at DICO Co.).
* **JLPT N2 study planning** — Came back to this topic multiple times; choosing between apps (Bunpro vs JPDB vs Renshuu), structuring a 365-day study plan.
* **Business automation** — Booking system logic for Rumah Labuh (pricing, payment handling, WhatsApp notifications) required multiple rounds of feature design.
* **Dataset finding** — Spent significant effort finding datasets with triple annotation comparable to IKEA ASM.

---

## 6. Communication Style & Preferences

* **Direct and efficient** — Doesn't want long preambles. Gets to the point and expects the same.
* **Prefers specifics over generics** — "Not generic. Use real examples." (literally the instruction for this document)
* **Evidence-based** — Rigorous fact-checking matters. Was bothered enough by fabricated benchmarks to audit 17 papers himself.
* **Appreciates structure, but not over-formatting** — Prefers prose over bullet-point dumps for explanations. Headers OK, excessive nesting is not.
* **Multi-domain simultaneously** — Often context-switches between thesis, business, career, and language learning in the same conversation period.
* **Single-file preference carries over to communication** — Wants consolidated answers, not scattered ones.
* **Works in Indonesian and English** — Business content (Rumah Labuh site) is in Indonesian; academic/tech work is in English.

---

## 7. Decisions Worth Remembering

* **Thesis architecture locked:** ResNet-50 + FPN + FiLM — this is intentional, not a constraint. The decision to route C5 directly to FiLM (bypassing FPN) is deliberate and has been explained.
* **Activity head always `[B, 2304]`** — This is a fixed design decision, not a variable.
* **γ uses `1 + tanh`** — Not pure tanh, not sigmoid. This distinction matters.
* **Rumah Labuh is live and operational** — This isn't a side project; it's a real business with real customers.
* **MEXT scholarship holder** — Financial and visa situation tied to SIT enrollment; academic timelines matter practically.
* **Positioned himself as a "Bridge Candidate"** for UNIQLO — This framing stuck and reflects a genuine self-understanding.
* **Chose Bunpro + JPDB + Renshuu combo** for Japanese — deliberate tool stack, not random.

---

## 8. Mistakes / Misconceptions That Got Corrected

* **Soft-argmax boundary bias** — Initial implementation had this bug; fixed by adjusting how grid coordinates were computed near borders.
* **Anchor ordering (ratios vs scales)** — Had ratios-inner/scales-outer; corrected to ratios-outer/scales-inner to match RetinaNet convention.
* **`log_var_pose` initialization** — Was initialized at 0.0; corrected to -1.0 to start with reasonable uncertainty priors.
* **`self.samples` not being populated** — Bug where the sample list stayed empty; fixed to ensure proper data flow.
* **Benchmark trust** — Initially approached benchmark papers with standard academic trust; empirical audit revealed this trust was misplaced for IKEA ASM comparisons specifically.
* **AquaCast data assumptions** — Several of the 30+ factual claims in early versions required correction after rigorous sourcing check.

---

## 9. Goals & Ambitions

### Short-Term (2025–2026)
* Complete and defend WorkerNet / POPW thesis at SIT
* Achieve JLPT N2 certification
* Scale Rumah Labuh booking system and occupancy
* Secure part-time or internship work in Tokyo (English-speaking preferred)

### Medium-Term
* Graduate from SIT with a strong publication/portfolio record
* Enter the Japanese job market in a data science, ML engineering, or tech role
* Potentially pursue ADB-Japan Scholarship at Keio University or equivalent
* Bridge Indonesia ↔ Japan professionally (career positioning)

### Long-Term
* Become a researcher or senior practitioner in applied deep learning / computer vision
* Grow Rumah Labuh into a larger property business passively
* Maintain dual footing in Indonesia and Japan professionally

---

## 10. Things Bashara Cares Deeply About

* **Rigor and accuracy** — Will not accept vague or unverifiable claims. Audited 17 papers when he had doubts. Asked for fact-checks on 30+ AquaCast claims. This is consistent.
* **Practical impact** — Every project has a real-world use case: POPW is for worker evaluation, AquaCast is for CPG demand ops, Rumah Labuh serves real tenants.
* **Independence and ownership** — Runs two businesses at 20-something years old while on a scholarship. Not waiting to be given a path.
* **Japan as a context, not just a location** — MEXT scholar, studying Japanese aggressively, applied for local jobs, exploring postgrad programs in Japan. It's deliberate.
* **Efficient systems** — Whether it's the boarding house booking flow or the thesis architecture, wants things clean, automated, and minimal in complexity.
* **Academic credibility** — Cares about ResearchGate presence, proper attribution, correct benchmarking. Not someone who cuts corners on citations.

---

## 11. Miscellaneous (Useful Context)

* **Clash of Clans player** — Has asked for detailed strategic guidance on the game. Takes it seriously.
* **Medium blogger** — Topics: credit risk ML, social media analytics, sales optimization, data engineering. Writes in English.
* **LeetCode practice** — Python, ongoing. Competitive programming is part of the prep routine.
* **HackerRank profile** — `bashara_aina`
* **Email:** bashara.aina.56@gmail.com
* **WhatsApp (business):** +62 851-9001-9083 (used for Rumah Labuh admin)
* **Persona:** Describes himself as "motivated in data engineering and analytics... I learn everything" — this matches observed behavior.

---

*This profile reflects patterns observed across many conversations. It should be treated as a living document — update when major decisions shift or new projects emerge.*
