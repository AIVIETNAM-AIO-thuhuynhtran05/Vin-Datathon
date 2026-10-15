"""Màu và style matplotlib dùng chung cho biểu đồ customer segmentation."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Bảng màu phân loại (thứ tự cố định, không xoay vòng) — tối đa 8 cụm.
CLUSTER_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"

SEQUENTIAL = LinearSegmentedColormap.from_list("blue", ["#cde2fb", "#86b6ef", "#2a78d6", "#1c5cab", "#0d366b"])
DIVERGING = LinearSegmentedColormap.from_list("blue_red", ["#2a78d6", "#f0efec", "#e34948"])


def apply_style() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "savefig.facecolor": SURFACE,
            "axes.edgecolor": BASELINE,
            "axes.labelcolor": INK_SECONDARY,
            "axes.titlecolor": INK,
            "axes.titlesize": 11,
            "axes.titleweight": "bold",
            "axes.labelsize": 9,
            "axes.grid": True,
            "axes.axisbelow": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.frameon": False,
            "legend.fontsize": 8,
            "font.size": 9,
        }
    )


def cluster_color(position: int) -> str:
    """Màu theo vị trí cụm; cụm thứ 9 trở đi gộp màu xám 'khác'."""
    return CLUSTER_COLORS[position] if position < len(CLUSTER_COLORS) else MUTED


def annotate_heatmap(axis: plt.Axes, values, labels, *, threshold: float) -> None:
    """Ghi giá trị lên từng ô; chữ trắng trên ô đậm."""
    for row in range(values.shape[0]):
        for column in range(values.shape[1]):
            axis.text(
                column, row, labels[row][column], ha="center", va="center", fontsize=8,
                color="white" if abs(values[row, column]) > threshold else INK,
            )
