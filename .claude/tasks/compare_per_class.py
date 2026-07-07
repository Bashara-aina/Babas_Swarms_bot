"""
Per-class accuracy comparison: MViTv2-S linear probe vs ConvNeXt MLP.
Reads existing JSON results, produces comparison JSON and markdown.
"""
import json
import os

MVIT_JSON = "/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/runs/rf_stages/checkpoints/activity_mvit_probe/per_class.json"
OUT_DIR = "/media/newadmin/master/POPW/working/code/industreal_improved/code/industreal_improved/src/runs/rf_stages/checkpoints/mvit_per_class"

# Load MViTv2-S data
with open(MVIT_JSON) as f:
    mvit_data = json.load(f)

# ConvNeXt per-class accuracy from the report
convnext_data = {
    "take_short_brace": 0.0875,
    "align_objects": 0.0,
    "take_pin_short": 0.0,
    "plug_short_pin": 0.0,
    "take_tooth_washer": 0.0040,
    "take_nut": 0.0,
    "tighten_nut": 0.0,
    "check_instruction": 0.0,
    "take_partial_model": 0.0472,
    "take_long_brace": 0.1010,
    "take_screw_pin": 0.0,
    "put": 0.6429,
    "take_pin_long": 0.5044,
    "put_pin_long": 0.0,
    "take_wing_beam": 0.0952,
    "plug_screw_pin": 0.0,
    "take_round_washer": 0.0,
    "take_acorn_nut": 0.0,
    "tighten_acorn_nut": 0.0,
    "take_pin_middle": 0.0,
    "take_wheel": 0.0,
    "plug_pin_long": 0.0526,
    "take_wing": 0.0472,
    "put_wing": 0.0,
    "plug_pin_middle": 0.0406,
    "take_pulley": 0.0,
    "browse_instruction": 0.4160,
    "fit_short_brace": 0.0149,
    "fit_tooth_washer": 0.0,
    "fit_round_washer": 0.0,
    "fit_long_brace": 0.0154,
    "fit_nut": 0.0,
    "put_screw_pin": 0.0,
    "put_wheel": 0.3317,
    "pull_wheel": 0.0,
    "loosen_nut": 0.0,
    "put_nut": 0.0,
    "pull_objects": 0.0,
    "put_pin_middle": 0.0,
    "take_objects": 0.0,
    "put_partial_model": 0.1199,
    "put_objects": 0.0,
    "pull_pin_short": 0.0,
    "put_pin_short": 0.0787,
    "put_long_brace": 0.0,
    "fit_wheel": 0.0,
    "check_partial_model": 0.0672,
    "fit_objects": 0.0,
    "put_round_washer": 0.0,
    "fit_pulley": 0.0,
    "fit_wing_beam": 0.1176,
    "put_tooth_washer": 0.0,
    "pull_pin_middle": 0.6207,
    "put_pulley": 0.0988,
    "pull_screw_pin": 0.0,
    "loosen_acorn_nut": 0.0,
    "take_small_screw_pin": 0.0,
    "plug_small_screw_pin": 0.0,
    "put_small_screw_pin": 0.1176,
    "fit_acorn_nut": 0.0,
    "fit_wing": 0.0305,
    "plug_objects": 0.0,
    "put_acorn_nut": 0.0,
}

# Build comparison
comparison = {}
for cls_name, mvit_acc in mvit_data.items():
    conv_acc = convnext_data.get(cls_name, None)
    mvit_acc_val = mvit_acc["accuracy"]
    mvit_count = mvit_acc["count"]

    if conv_acc is not None:
        delta = mvit_acc_val - conv_acc
    else:
        conv_acc = None
        delta = None

    comparison[cls_name] = {
        "mvit_accuracy": round(mvit_acc_val, 6),
        "mvit_count": mvit_count,
        "convnext_accuracy": round(conv_acc, 6) if conv_acc is not None else None,
        "delta": round(delta, 6) if delta is not None else None,
        "zero_to_nonzero": conv_acc is not None and conv_acc == 0.0 and mvit_acc_val > 0.0
    }

# Also add ConvNeXt-only classes
for cls_name, conv_acc in convnext_data.items():
    if cls_name not in comparison:
        comparison[cls_name] = {
            "mvit_accuracy": None,
            "mvit_count": None,
            "convnext_accuracy": round(conv_acc, 6),
            "delta": None,
            "zero_to_nonzero": False
        }

# Save JSON
os.makedirs(OUT_DIR, exist_ok=True)
with open(os.path.join(OUT_DIR, "comparison.json"), "w") as f:
    json.dump(comparison, f, indent=2)

# --- Build MD report ---

classes_with_delta = [(n, d) for n, d in comparison.items() if d["delta"] is not None]
classes_with_delta.sort(key=lambda x: x[1]["delta"], reverse=True)

mvit_nonzero = sum(1 for c in comparison.values() if c["mvit_accuracy"] is not None and c["mvit_accuracy"] > 0)
conv_nonzero = sum(1 for c in comparison.values() if c["convnext_accuracy"] is not None and c["convnext_accuracy"] > 0)

zero_to_nonzero = [n for n, c in comparison.items() if c.get("zero_to_nonzero")]
fixed_count = len(zero_to_nonzero)

conv_zeros = [n for n, c in comparison.items() if c["convnext_accuracy"] is not None and c["convnext_accuracy"] == 0.0]
conv_zero_count = len(conv_zeros)

mvit_accs = [c["mvit_accuracy"] for c in comparison.values() if c["mvit_accuracy"] is not None]
conv_accs = [c["convnext_accuracy"] for c in comparison.values() if c["convnext_accuracy"] is not None]

mvit_mean = sum(mvit_accs) / len(mvit_accs) if mvit_accs else 0
conv_mean = sum(conv_accs) / len(conv_accs) if conv_accs else 0

top5_improved = classes_with_delta[:5]

got_worse = [(n, d) for n, d in classes_with_delta if d["delta"] < 0]
got_worse.sort(key=lambda x: x[1]["delta"])

lines = []
lines.append("# Per-Class Accuracy Comparison: MViTv2-S Linear Probe vs ConvNeXt MLP (Opus 144)")
lines.append("")
lines.append(f"**Date:** 2026-07-07")
lines.append(f"**MViTv2-S overall top-1:** 0.3810")
lines.append(f"**ConvNeXt overall top-1:** 0.0236")
lines.append(f"**Mean per-class accuracy (MViTv2-S):** {mvit_mean:.4f}")
lines.append(f"**Mean per-class accuracy (ConvNeXt):** {conv_mean:.4f}")
lines.append("")

lines.append("## Summary")
lines.append("")
lines.append(f"- **Classes with non-zero accuracy (MViTv2-S):** {mvit_nonzero}")
lines.append(f"- **Classes with non-zero accuracy (ConvNeXt):** {conv_nonzero}")
lines.append(f"- **ConvNeXt zero-accuracy classes:** {conv_zero_count}")
lines.append(f"- **Zero-to-nonzero transitions:** {fixed_count}")
lines.append(f"- **Classes MViTv2-S still at 0.0:** {sum(1 for c in comparison.values() if c['mvit_accuracy'] is not None and c['mvit_accuracy'] == 0.0)}")
lines.append("")

lines.append("## Top-10 Most Improved Classes (Largest Delta)")
lines.append("")
lines.append("| Class | ConvNeXt | MViTv2-S | Delta | MViTv2-S Count |")
lines.append("|-------|----------|----------|-------|----------------|")
for i, (name, c) in enumerate(classes_with_delta[:10]):
    lines.append(f"| {name} | {c['convnext_accuracy']:.4f} | {c['mvit_accuracy']:.4f} | +{c['delta']:.4f} | {c['mvit_count']} |")
lines.append("")

lines.append("## Zero-to-Nonzero Transitions")
lines.append("")
lines.append("| Class | MViTv2-S Accuracy | MViTv2-S Count | Delta |")
lines.append("|-------|-------------------|----------------|-------|")
for name in sorted(zero_to_nonzero, key=lambda n: comparison[n]["mvit_accuracy"], reverse=True):
    c = comparison[name]
    lines.append(f"| {name} | {c['mvit_accuracy']:.4f} | {c['mvit_count']} | +{c['delta']:.4f} |")
lines.append("")

lines.append("## Classes That Worsened")
lines.append("")
if got_worse:
    lines.append("| Class | ConvNeXt | MViTv2-S | Delta | MViTv2-S Count |")
    lines.append("|-------|----------|----------|-------|----------------|")
    for name, c in got_worse:
        lines.append(f"| {name} | {c['convnext_accuracy']:.4f} | {c['mvit_accuracy']:.4f} | {c['delta']:.4f} | {c['mvit_count']} |")
else:
    lines.append("(None)")
lines.append("")

lines.append("## Full Comparison Table (All Matched Classes)")
lines.append("")
lines.append("| Class | ConvNeXt | MViTv2-S | Delta | Fixed? |")
lines.append("|-------|----------|----------|-------|--------|")
for name, c in sorted(classes_with_delta, key=lambda x: x[0]):
    z2n = "YES" if c.get("zero_to_nonzero") else ""
    lines.append(f"| {name} | {c['convnext_accuracy']:.4f} | {c['mvit_accuracy']:.4f} | +{c['delta']:.4f} | {z2n} |")
lines.append("")

lines.append("## MViTv2-S Only Classes")
lines.append("")
mvit_only = [(n, c) for n, c in comparison.items() if c["convnext_accuracy"] is None]
if mvit_only:
    lines.append("| Class | MViTv2-S Accuracy | Count |")
    lines.append("|-------|-------------------|-------|")
    for name, c in sorted(mvit_only, key=lambda x: x[0]):
        lines.append(f"| {name} | {c['mvit_accuracy']:.4f} | {c['mvit_count']} |")
lines.append("")

lines.append("## ConvNeXt Only Classes")
lines.append("")
conv_only = [(n, c) for n, c in comparison.items() if c["mvit_accuracy"] is None]
if conv_only:
    lines.append("| Class | ConvNeXt Accuracy |")
    lines.append("|-------|-------------------|")
    for name, c in sorted(conv_only, key=lambda x: x[0]):
        lines.append(f"| {name} | {c['convnext_accuracy']:.4f} |")
lines.append("")

md_content = "\n".join(lines)
md_path = os.path.join(OUT_DIR, "comparison.md")
with open(md_path, "w") as f:
    f.write(md_content)

# Print key stats for the commit message
print("=== KEY FINDINGS ===")
print(f"Top-5 most improved:")
for i, (name, c) in enumerate(top5_improved):
    print(f"  {i+1}. {name}: {c['convnext_accuracy']:.4f} -> {c['mvit_accuracy']:.4f} (+{c['delta']:.4f})")
print(f"\nZero-to-nonzero: {fixed_count}/{conv_zero_count} ConvNeXt zeros fixed")
print(f"List of fixed: {zero_to_nonzero}")
print(f"Classes that worsened:")
for name, c in got_worse:
    print(f"  {name}: {c['convnext_accuracy']:.4f} -> {c['mvit_accuracy']:.4f} ({c['delta']:.4f})")
print(f"\nMean per-class accuracy: ConvNeXt {conv_mean:.4f} -> MViTv2-S {mvit_mean:.4f}")
