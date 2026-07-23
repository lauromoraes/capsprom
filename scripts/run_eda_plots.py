"""Regenerate SVG figures from existing CapsProm EDA CSV artifacts."""

from pathlib import Path

from capsprom.eda.plots import generate_eda_figures, write_figure_report


def main() -> None:
    """Generate EDA figures using the default strict-DNA EDA output directory."""

    output_dir = Path("outputs/eda/intra_strict_feature_exploration")
    figures = generate_eda_figures(output_dir)
    write_figure_report(output_dir, figures)


if __name__ == "__main__":
    main()
