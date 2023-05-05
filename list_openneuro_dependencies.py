# list the number of subjects
# in openneuro derivatives (fmriprep, mriqc, freesurfer)
# either on openneuro proper or in openneuro-derivatives


import json
from pathlib import Path

import datalad.api as dlapi
from rich import print

VERBOSE = False
DEBUG = False

URL_BASE_OPENNEURO_DERIVATIVES = "https://github.com/OpenNeuroDerivatives/"
URL_BASE_OPENNEURO = "https://github.com/OpenNeuroDatasets/"


def main():
    datasets = {}

    datalad_superdataset = Path("/home/remi/datalad/datasets.datalad.org")

    openneuro = datalad_superdataset / "openneuro"
    install_dataset(openneuro, verbose=VERBOSE)

    openneuro_derivatives = datalad_superdataset / "openneuro-derivatives"
    install_dataset(openneuro_derivatives, verbose=VERBOSE)

    fmriprep_datasets = list(openneuro_derivatives.glob("*fmriprep"))
    datasets = update_from_fmriprep_datasets(fmriprep_datasets, datasets)

    mriqc_datasets = list(openneuro_derivatives.glob("*mriqc"))
    datasets = update_from_mriqc_datasets(mriqc_datasets, datasets)

    with open(Path(__file__).resolve().parent / "openneuro_derivatives.json", "w") as f:
        json.dump(datasets, f, indent=4)

    print(f"Number of datasets: {len(datasets)}")
    print(f"Number of subjects: {sum(v['nb_subjects'] for v in datasets.values())}")
    for der in ["fmriprep", "mriqc", "freesurfer"]:
        print(f"Number of dataset with {der}: {nb_datasets_with(datasets, der)}")
        nb_subjects_for_der = sum(
            v["nb_subjects"] for v in datasets.values() if v[der] is not None
        )
        print(f"  Corresponding to {nb_subjects_for_der} subjects")
    print(
        "Number of datasets with participants.tsv: "
        f"{nb_datasets_with(datasets, 'has_participant_tsv')}"
    )


def nb_datasets_with(datasets, key):
    return sum(v[key] not in [None, False] for v in datasets.values())


def update_from_fmriprep_datasets(fmriprep_datasets, datasets):
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

    return datasets


def update_from_mriqc_datasets(mriqc_datasets, datasets):
    for i, dataset_ in enumerate(mriqc_datasets):
        if DEBUG and i > 5:
            break

        dataset_name = dataset_.name.replace("-mriqc", "")

        if datasets.get(dataset_name) is None:
            datasets[dataset_name] = new_datatset(dataset_name)

            datasets[dataset_name]["mriqc"] = f"{URL_BASE_OPENNEURO_DERIVATIVES}{dataset_.name}"

            datasets[dataset_name]["nb_subjects"] = get_nb_subjects(dataset_)

            datasets = check_participants_tsv(datasets, dataset_, dataset_name)

        else:
            datasets[dataset_name]["mriqc"] = f"{URL_BASE_OPENNEURO_DERIVATIVES}{dataset_.name}"

    return datasets


def install_dataset(dataset_pth, verbose):
    dl_dataset = dlapi.Dataset(dataset_pth)
    if not dl_dataset.is_installed():
        if verbose:
            print(f"installing: {dataset_pth}")
        dl_dataset.install()
    else:
        if verbose:
            print(f"{dataset_pth} already installed")


def new_datatset(name):
    return {
        "name": name,
        "has_participant_tsv": None,
        "nb_subjects": None,
        "raw": f"{URL_BASE_OPENNEURO}{name}",
        "fmriprep": None,
        "freesurfer": None,
        "mriqc": None,
    }


def get_nb_subjects(pth):
    tmp = [v for v in pth.glob("sub-*") if v.is_dir()]
    return len(tmp)


def check_participants_tsv(datasets, dataset_, dataset_name):
    raw_dataset = dataset_ / "sourcedata" / "raw"
    if (raw_dataset / "participants.tsv").exists():
        datasets[dataset_name]["has_participant_tsv"] = True
    else:
        if VERBOSE:
            print(f"{dataset_.name}: No raw dataset found.")
        datasets[dataset_name]["has_participant_tsv"] = False
    return datasets


if __name__ == "__main__":
    main()
