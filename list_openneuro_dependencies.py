# list the number of subjects
# in openneuro derivatives (fmriprep, mriqc, freesurfer)
# either on openneuro proper or in openneuro-derivatives


import json
from pathlib import Path

import datalad.api as dlapi
from rich import print

VERBOSE = False
DEBUG = False

URL_BASE_OPENNEURO = "https://github.com/OpenNeuroDatasets/"
URL_BASE_OPENNEURO_DERIVATIVES = "https://github.com/OpenNeuroDerivatives/"


def main():
    datalad_superdataset = Path("/home/remi/datalad/datasets.datalad.org")

    datasets = {}
    datasets = list_openneuro(datalad_superdataset, datasets)
    print(f"derivatives from openneuro: {URL_BASE_OPENNEURO}")
    print(f"from {nb_datasets(datalad_superdataset / 'openneuro')} datasets")
    with open(Path(__file__).resolve().parent / "openneuro.json", "w") as f:
        json.dump(datasets, f, indent=4)
    print_results(datasets)

    datasets = {}
    datasets = list_openneuro_derivatives(datalad_superdataset, datasets)
    print(f"from openneuro-derivatives: {URL_BASE_OPENNEURO_DERIVATIVES}")
    print(f"from {nb_datasets(datalad_superdataset / 'openneuro-derivatives')} datasets")
    print_results(datasets)
    with open(Path(__file__).resolve().parent / "openneuro_derivatives.json", "w") as f:
        json.dump(datasets, f, indent=4)


def nb_datasets(pth: Path):
    return len(list(pth.glob("ds*")))


def has_mri(bids_pth: Path):
    return bids_pth.glob("sub*/func") or bids_pth.glob("sub*/ses*/func")


def list_openneuro(datalad_superdataset: Path, datasets: dict[str, dict[str, str]]):
    openneuro = datalad_superdataset / "openneuro"
    install_dataset(openneuro, verbose=VERBOSE)

    raw_datasets = list(openneuro.glob("ds*"))

    for dataset_ in raw_datasets:
        if has_mri(dataset_) and (dataset_ / "participants.tsv").exists():
            dataset_name = dataset_.name
            if datasets.get(dataset_name) is None:
                datasets[dataset_name] = new_datatset(dataset_name)
            datasets[dataset_name]["has_participant_tsv"] = True
            datasets[dataset_name]["has_phenotype_dir"] = bool((dataset_ / "phenotype").exists())
            datasets[dataset_name]["nb_subjects"] = get_nb_subjects(dataset_)

    for der in [
        "fmriprep",
        "freesurfer",
        "mriqc",
    ]:
        der_datasets = list(openneuro.glob(f"*/derivatives/*{der}"))
        for dataset_ in der_datasets:
            raw_dataset = dataset_.parents[1]
            dataset_name = raw_dataset.name
            if datasets.get(dataset_name) is None:
                datasets[dataset_name] = new_datatset(dataset_name)
            datasets[dataset_name]["has_participant_tsv"] = bool(
                (raw_dataset / "participants.tsv").exists()
            )
            datasets[dataset_name]["has_phenotype_dir"] = bool(
                (raw_dataset / "phenotype").exists()
            )
            datasets[dataset_name]["nb_subjects"] = get_nb_subjects(dataset_)
            datasets[dataset_name][der] = f"{URL_BASE_OPENNEURO}{dataset_.name}"

    return datasets


def list_openneuro_derivatives(datalad_superdataset: Path, datasets: dict[str, dict[str, str]]):
    openneuro_derivatives = datalad_superdataset / "openneuro-derivatives"

    install_dataset(openneuro_derivatives, verbose=VERBOSE)

    fmriprep_datasets = list(openneuro_derivatives.glob("*fmriprep"))
    datasets = update_from_fmriprep_datasets(fmriprep_datasets, datasets)

    mriqc_datasets = list(openneuro_derivatives.glob("*mriqc"))
    datasets = update_from_mriqc_datasets(mriqc_datasets, datasets)

    return datasets


def print_results(datasets: dict[str, dict[str, str]]):
    print(f"\tNumber of datasets: {len(datasets)}")
    print(f"\tNumber of subjects: {sum(v['nb_subjects'] for v in datasets.values())}")
    print(
        "\tNumber of datasets with participants.tsv: "
        f"{nb_datasets_with(datasets, 'has_participant_tsv')}"
    )
    print(
        "\tNumber of datasets have phenotype dir: "
        f"{nb_datasets_with(datasets, 'has_phenotype_dir')}"
    )
    for der in [
        "fmriprep",
        "freesurfer",
        "mriqc",
    ]:
        print(f"\tNumber of dataset with {der}: {nb_datasets_with(datasets, der)}")
        nb_subjects_for_der = sum(
            v["nb_subjects"] for v in datasets.values() if v[der] is not None
        )
        print(f"\t\tCorresponding to {nb_subjects_for_der} subjects")


def nb_datasets_with(datasets: dict[str, dict[str, str]], key: str):
    return sum(v[key] not in [None, False] for v in datasets.values())


def update_from_fmriprep_datasets(
    fmriprep_datasets, datasets: dict[str, dict[str, str]]
) -> dict[str, dict[str, str]]:
    for i, dataset_ in enumerate(fmriprep_datasets):
        if DEBUG and i > 5:
            break

        install_dataset(dataset_, verbose=VERBOSE)

        dataset_name = dataset_.name.replace("-fmriprep", "")

        if datasets.get(dataset_name) is None:
            datasets[dataset_name] = new_datatset(dataset_name)

        datasets[dataset_name]["fmriprep"] = f"{URL_BASE_OPENNEURO_DERIVATIVES}{dataset_.name}"

        datasets[dataset_name]["nb_subjects"] = get_nb_subjects(dataset_)

        if (dataset_ / "sourcedata" / "freesurfer").exists():
            datasets[dataset_name][
                "freesurfer"
            ] = f"{datasets[dataset_name]['fmriprep']}/tree/main/sourcedata/freesurfer"

        datasets = check_participants_tsv(datasets, dataset_, dataset_name)
        datasets = check_phenotype_dir(datasets, dataset_, dataset_name)

    return datasets


def update_from_mriqc_datasets(
    mriqc_datasets, datasets: dict[str, dict[str, str]]
) -> dict[str, dict[str, str]]:
    for i, dataset_ in enumerate(mriqc_datasets):
        if DEBUG and i > 5:
            break

        dataset_name = dataset_.name.replace("-mriqc", "")

        if datasets.get(dataset_name) is None:
            datasets[dataset_name] = new_datatset(dataset_name)

            datasets[dataset_name]["mriqc"] = f"{URL_BASE_OPENNEURO_DERIVATIVES}{dataset_.name}"

            datasets[dataset_name]["nb_subjects"] = get_nb_subjects(dataset_)

            datasets = check_participants_tsv(datasets, dataset_, dataset_name)
            datasets = check_phenotype_dir(datasets, dataset_, dataset_name)

        else:
            datasets[dataset_name]["mriqc"] = f"{URL_BASE_OPENNEURO_DERIVATIVES}{dataset_.name}"

    return datasets


def install_dataset(dataset_pth: Path, verbose: bool) -> None:
    dl_dataset = dlapi.Dataset(dataset_pth)
    if not dl_dataset.is_installed():
        if verbose:
            print(f"installing: {dataset_pth}")
        dl_dataset.install()
    else:
        if verbose:
            print(f"{dataset_pth} already installed")


def new_datatset(name: str) -> dict[str, str]:
    return {
        "name": name,
        "has_participant_tsv": None,
        "nb_subjects": None,
        "raw": f"{URL_BASE_OPENNEURO}{name}",
        "fmriprep": None,
        "freesurfer": None,
        "mriqc": None,
    }


def get_nb_subjects(pth: Path):
    tmp = [v for v in pth.glob("sub-*") if v.is_dir()]
    return len(tmp)


def check_participants_tsv(
    datasets: dict[str, dict[str, str]], dataset_: Path, dataset_name: str
) -> dict[str, dict[str, str]]:
    raw_dataset = dataset_ / "sourcedata" / "raw"
    datasets[dataset_name]["has_participant_tsv"] = bool(
        (raw_dataset / "participants.tsv").exists()
    )
    return datasets


def check_phenotype_dir(
    datasets: dict[str, dict[str, str]], dataset_: Path, dataset_name: str
) -> dict[str, dict[str, str]]:
    raw_dataset = dataset_ / "sourcedata" / "raw"
    datasets[dataset_name]["has_phenotype_dir"] = bool((raw_dataset / "phenotype").exists())
    return datasets


if __name__ == "__main__":
    main()
