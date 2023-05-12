from pathlib import Path

import pandas as pd
from rich import print


def main():
    print("**OpenNeuro datasets:**\n")
    datasets = pd.read_csv(Path(__file__).resolve().parent / "openneuro.tsv", sep="\t")
    datasets.fillna(False, inplace=True)
    print_results(datasets)

    print("\n\n**OpenNeuro derivatives datasets:**\n")
    datasets = pd.read_csv(Path(__file__).resolve().parent / "openneuro_derivatives.tsv", sep="\t")
    datasets.fillna(False, inplace=True)
    print_results(datasets)


def print_results(datasets):
    print(
        f"Number of datasets: {len(datasets)} with {datasets.nb_subjects.sum()} subjects including:"
    )
    print(f"- {datasets.has_mri.sum()} datasets with MRI data")
    mask = datasets.has_mri
    print(
        f" - with participants.tsv: {datasets[mask].has_participant_tsv.sum()} "
        f"({nb_participants_tsv_with_more_than_one_column(datasets[mask].participant_columns)} "
        "with more than 'participant_id' column)"
    )
    print(f" - with phenotype directory: {datasets[mask].has_phenotype_dir.sum()}")
    for der in [
        "fmriprep",
        "freesurfer",
        "mriqc",
    ]:
        mask = datasets[der] != False  # noqa
        print(f" - with {der}: {(mask).sum()} ({datasets[mask].nb_subjects.sum()} subjects)")
        print(f"   - with participants.tsv: {datasets[mask].has_participant_tsv.sum()}")
        print(f"   - with phenotype directory: {datasets[mask].has_phenotype_dir.sum()}")


def nb_participants_tsv_with_more_than_one_column(series):
    nb = sum(len(i) > 1 for i in series if not isinstance(i, bool))
    return nb


if __name__ == "__main__":
    main()
