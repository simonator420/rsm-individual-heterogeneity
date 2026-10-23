"""Rebuild the RSM figures using the RP house style.

The source data and model outputs are kept unchanged.  The script writes a
reviewable, separate figure set with editable SVG/PDF plus high-resolution
PNG/TIFF exports.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import gettempdir

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe
import numpy as np
import pandas as pd
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "pone.0219295.s001.csv"
MODEL = ROOT / "results"
OUT = ROOT / "results" / "figures"

# Shared RP palette used in the other manuscript figure scripts.
NAV = "#1c3557"
BLUE = "#2c5f8a"
VERMILLION = "#e69f00"  # color-blind-safe orange
PURPLE = "#756bb1"       # color-blind-safe purple
INK = "#262626"
MUTED = "#555555"
GRAY = "#7a7a7a"
LIGHT_GRAY = "#bdbdbd"
GRID = "#ebebeb"
SPINE = "#c4c4c4"

W_DOUBLE = 190 / 25.4  # 190 mm, the common two-column manuscript width.
BODY_TEXT_SIZE = 9.0
TICK_TEXT_SIZE = 8.0
PANEL_TITLE_SIZE = 11.0

TIME_MAP = {"P": 0.0, "30": 0.5, "60": 1.0, "180": 3.0, "360": 6.0, "24": 24.0, "48": 48.0}
POST_TIMES = [0.0, 0.5, 1.0, 3.0, 6.0, 24.0, 48.0]
TIME_LABELS = ["0", "0.5", "1", "3", "6", "24", "48"]


def register_helvetica_neue_bold() -> None:
    collection_path = Path("/System/Library/Fonts/HelveticaNeue.ttc")
    if not collection_path.exists():
        return
    try:
        from fontTools.ttLib import TTCollection

        font_path = Path(gettempdir()) / "rsm-figure-fonts" / "HelveticaNeue-Bold.ttf"
        if not font_path.exists():
            font_path.parent.mkdir(parents=True, exist_ok=True)
            TTCollection(collection_path).fonts[1].save(font_path)
        font_manager.fontManager.addfont(font_path)
    except Exception:
        pass


def apply_house_style() -> None:
    register_helvetica_neue_bold()
    mpl.rcParams.update(
        {
            "figure.dpi": 110,
            "savefig.dpi": 400,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.22,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans", "sans-serif"],
            "font.size": BODY_TEXT_SIZE,
            "axes.titlesize": PANEL_TITLE_SIZE,
            "axes.titleweight": "bold",
            "axes.titlecolor": INK,
            "axes.labelsize": BODY_TEXT_SIZE,
            "axes.labelpad": 7,
            "axes.titlepad": 9,
            "xtick.labelsize": TICK_TEXT_SIZE,
            "ytick.labelsize": TICK_TEXT_SIZE,
            "xtick.major.pad": 4,
            "ytick.major.pad": 4,
            "legend.fontsize": TICK_TEXT_SIZE,
            "legend.frameon": False,
            "axes.edgecolor": SPINE,
            "axes.linewidth": 0.7,
            "axes.labelcolor": INK,
            "text.color": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "xtick.major.width": 0.7,
            "ytick.major.width": 0.7,
            "xtick.major.size": 3,
            "ytick.major.size": 3,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.color": GRID,
            "grid.linewidth": 0.5,
            "grid.alpha": 1.0,
            "axes.axisbelow": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "lines.linewidth": 1.4,
            "lines.markersize": 4,
        }
    )
    OUT.mkdir(parents=True, exist_ok=True)


def add_panel_label(ax: plt.Axes, label: str, x: float = -0.12, y: float = 1.04) -> None:
    ax.text(
        x,
        y,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=10.5,
        fontweight="bold",
        color=INK,
        clip_on=False,
    )


def save_figure(fig: plt.Figure, stem: str) -> None:
    for ext in ("svg", "pdf"):
        fig.savefig(OUT / f"{stem}.{ext}", bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / f"{stem}.png", dpi=400, bbox_inches="tight", pad_inches=0.22, facecolor="white")
    tiff_path = OUT / f"{stem}.tif"
    fig.savefig(
        tiff_path,
        dpi=600,
        bbox_inches="tight",
        pad_inches=0.22,
        facecolor="white",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    with Image.open(tiff_path) as image:
        rgb = image.convert("RGB")
        rgb.save(tiff_path, format="TIFF", compression="tiff_lzw", dpi=(600, 600))
    plt.close(fig)


def prepare_trajectory_data() -> pd.DataFrame:
    raw = pd.read_csv(DATA)
    d = raw[
        raw["D.Training"].isin(["High", "Low", "Mod"])
        & (raw["D.Name"] != "Athlete 10")
    ].copy()
    d["time_raw"] = d["D.TimeAfterTraining"].astype(str)
    d["hours"] = d["time_raw"].map(TIME_MAP)
    baseline = (
        d.loc[d["time_raw"] == "1"]
        .groupby(["D.Name", "D.Training"])["D.MaxForceScaled"]
        .mean()
        .rename("baseline")
    )
    d = d.join(baseline, on=["D.Name", "D.Training"])
    d["relative_change"] = (d["D.MaxForceScaled"] / d["baseline"] - 1.0) * 100.0
    d = d[d["time_raw"].isin(TIME_MAP)].copy()
    return (
        d.groupby(["D.Name", "D.Training", "hours"], as_index=False)["relative_change"]
        .mean()
    )


def prepare_paired_contrasts() -> pd.DataFrame:
    """Compute the paired athlete-level High-minus-Low t intervals used in Fig. 2."""
    means = prepare_trajectory_data()
    wide = means.pivot_table(index=["D.Name", "hours"], columns="D.Training", values="relative_change")
    wide["difference"] = wide["High"] - wide["Low"]
    from scipy.stats import t

    rows = []
    for hours, group in wide.reset_index().groupby("hours"):
        values = group["difference"].dropna().to_numpy()
        estimate = float(np.mean(values))
        se = float(np.std(values, ddof=1) / np.sqrt(len(values)))
        half_width = float(t.ppf(0.975, len(values) - 1) * se)
        rows.append(
            {
                "time_h": hours,
                "estimate_high_minus_low_pp": estimate,
                "ci95_low_pp": estimate - half_width,
                "ci95_high_pp": estimate + half_width,
            }
        )
    return pd.DataFrame(rows).sort_values("time_h")


def figure_1() -> None:
    d = prepare_trajectory_data()
    workloads = [("Low", "Low", BLUE), ("Mod", "Moderate", VERMILLION), ("High", "High", PURPLE)]
    fig, axes = plt.subplots(3, 1, figsize=(W_DOUBLE, 8.25), sharex=True, sharey=True)
    x = np.arange(len(POST_TIMES))
    for ax, (workload, title, accent) in zip(axes, workloads):
        w = d[d["D.Training"] == workload]
        for athlete, g in w.groupby("D.Name", sort=True):
            y = g.set_index("hours")["relative_change"].reindex(POST_TIMES)
            ax.plot(
                x,
                y,
                color=LIGHT_GRAY,
                alpha=0.52,
                linewidth=0.70,
                marker="o",
                markersize=2.4,
                zorder=2,
            )
        mean = w.groupby("hours")["relative_change"].mean().reindex(POST_TIMES)
        ax.plot(
            x,
            mean,
            color=INK,
            linewidth=2.1,
            marker="o",
            markersize=4.3,
            markerfacecolor=accent,
            markeredgecolor=INK,
            markeredgewidth=0.75,
            zorder=5,
            path_effects=[pe.Stroke(linewidth=4.5, foreground="white"), pe.Normal()],
        )
        ax.axhline(0, color=GRAY, linewidth=0.8, linestyle=(0, (4, 3)), zorder=1)
        ax.set_title(title)
        ax.set_xticks(x)
        ax.set_xticklabels(TIME_LABELS)
        ax.set_xlim(-0.3, len(x) - 0.7)
        ax.grid(axis="y")
        ax.grid(axis="x", visible=False)
        ax.spines["left"].set_color(SPINE)
        ax.spines["bottom"].set_color(SPINE)
        ax.spines["left"].set_linewidth(0.7)
        ax.spines["bottom"].set_linewidth(0.7)
    axes[0].set_ylabel("Relative peak-force change (%)")
    axes[1].set_ylabel("Relative peak-force change (%)")
    axes[2].set_ylabel("Relative peak-force change (%)")
    axes[2].set_xlabel("Hours after exercise")
    axes[0].set_ylim(-16, 16)
    add_panel_label(axes[0], "A")
    add_panel_label(axes[1], "B")
    add_panel_label(axes[2], "C")
    handles = [
        Line2D([0], [0], color=LIGHT_GRAY, marker="o", markersize=3.2, linewidth=0.85, label="Individual athletes (n = 9)"),
        Line2D([0], [0], color=INK, marker="o", markerfacecolor=NAV, markeredgecolor=INK, markersize=4.2, linewidth=2.1, label="Mean across athletes"),
    ]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.015), ncol=2, handletextpad=0.55, columnspacing=1.6)
    fig.subplots_adjust(left=0.12, right=0.985, top=0.96, bottom=0.10, hspace=0.30)
    save_figure(fig, "RSM_Figure_1_Athlete_Trajectories_house_style")


def figure_2() -> None:
    d = pd.read_csv(MODEL / "primary_high_low_contrasts.csv")
    paired = prepare_paired_contrasts()
    y = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(W_DOUBLE, 4.7))
    ax.axvline(0, color=GRAY, linewidth=0.9, linestyle=(0, (4, 3)), zorder=1)
    ax.errorbar(
        d["estimate_high_minus_low_pp"], y + 0.11,
        xerr=[d["estimate_high_minus_low_pp"] - d["ci95_low_pp"], d["ci95_high_pp"] - d["estimate_high_minus_low_pp"]],
        fmt="o", color=BLUE, markerfacecolor=BLUE, markeredgecolor="white", markeredgewidth=0.6,
        markersize=4.8, linewidth=1.4, capsize=2.5, label="Mixed-model Wald CI", zorder=3,
    )
    ax.errorbar(
        paired["estimate_high_minus_low_pp"], y - 0.11,
        xerr=[paired["estimate_high_minus_low_pp"] - paired["ci95_low_pp"], paired["ci95_high_pp"] - paired["estimate_high_minus_low_pp"]],
        fmt="s", color=VERMILLION, markerfacecolor=VERMILLION, markeredgecolor="white", markeredgewidth=0.6,
        markersize=4.2, linewidth=1.2, capsize=2.5, label="Paired athlete-level t CI", zorder=2,
    )
    labels = ["Immediately", "0.5 h", "1 h", "3 h", "6 h", "24 h", "48 h"]
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("High minus Low: percentage-point difference (95% CI)")
    ax.set_xlim(-9.2, 9.2)
    ax.grid(axis="x")
    ax.grid(axis="y", visible=False)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.025),
        ncol=2,
        handletextpad=0.55,
        columnspacing=1.6,
    )
    fig.subplots_adjust(left=0.13, right=0.985, top=0.96, bottom=0.25)
    save_figure(fig, "RSM_Figure_2_High_Low_Contrasts_house_style")


def figure_3() -> None:
    d = pd.read_csv(MODEL / "loao_fold_summary.csv")
    ids = d["held_out_athlete"].str.extract(r"(\d+)")[0].astype(int)
    x = np.arange(len(d))
    fig, axes = plt.subplots(1, 2, figsize=(W_DOUBLE, 3.55), gridspec_kw={"wspace": 0.28})
    axes[0].bar(x, d["rmse_pp"], color=BLUE, edgecolor=INK, linewidth=0.45, width=0.72)
    axes[0].set_title("Prediction error")
    axes[0].set_ylabel("RMSE (percentage points)")
    axes[0].set_ylim(0, 9.1)
    axes[0].set_yticks([0, 2, 4, 6, 8])
    axes[1].bar(x, d["coverage_95"] * 100, color=PURPLE, edgecolor=INK, linewidth=0.45, width=0.72)
    axes[1].axhline(95, color=INK, linewidth=1.0, linestyle=(0, (4, 3)))
    axes[1].set_title("Nominal 95% prediction intervals")
    axes[1].set_ylabel("Empirical interval coverage (%)")
    axes[1].set_ylim(0, 108)
    axes[1].set_yticks([0, 20, 40, 60, 80, 100])
    for ax in axes:
        ax.set_xticks(x)
        ax.set_xticklabels(ids)
        ax.set_xlabel("Held-out athlete")
        ax.grid(axis="y")
        ax.grid(axis="x", visible=False)
        ax.spines["left"].set_color(SPINE)
        ax.spines["bottom"].set_color(SPINE)
    add_panel_label(axes[0], "A")
    add_panel_label(axes[1], "B")
    fig.subplots_adjust(left=0.095, right=0.985, top=0.83, bottom=0.22)
    save_figure(fig, "RSM_Figure_3_LOAO_Performance_house_style")


def main() -> None:
    apply_house_style()
    figure_1()
    figure_2()
    figure_3()
    print(f"Saved house-style figures to {OUT}")


if __name__ == "__main__":
    main()
