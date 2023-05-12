from pathlib import Path

import pandas as pd
from rich import print


def main():
    datasets = pd.read_csv(Path(__file__).resolve().parent / "openneuro.tsv", sep="\t")
    datasets.fillna(False, inplace=True)

    print_results(datasets)

    datasets = pd.read_csv(Path(__file__).resolve().parent / "openneuro_derivatives.tsv", sep="\t")
    datasets.fillna(False, inplace=True)

    print_results(datasets)


def print_results(datasets):
    print(
        f"Number of datasets: {len(datasets)} with {datasets.nb_subjects.sum()} subjects including:"
    )
    print(f"\t- {datasets.has_mri.sum()} datasets with MRI data")
    mask = datasets.has_mri
    print(f"\t - with participants.tsv: {datasets[mask].has_participant_tsv.sum()}")
    print(f"\t - with phenotype directory: {datasets[mask].has_phenotype_dir.sum()}")
    for der in [
        "fmriprep",
        "freesurfer",
        "mriqc",
    ]:
        mask = datasets[der] != False  # noqa
        print(f"\t - with {der}: {(mask).sum()} ({datasets[mask].nb_subjects.sum()} subjects)")
        print(f"\t   - with participants.tsv: {datasets[mask].has_participant_tsv.sum()}")
        print(f"\t   - with phenotype directory: {datasets[mask].has_phenotype_dir.sum()}")


def nb_datasets_with(datasets: dict[str, dict[str, str]], key: str):
    return sum(v[key] not in [None, False] for v in datasets.values())


if __name__ == "__main__":
    main()
