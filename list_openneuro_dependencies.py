# list datasets contents either on openneuro proper or in openneuro-derivatives
# and write the results in a tsv file

from pathlib import Path
from warnings import warn

import datalad.api as dlapi
import pandas as pd
from rich import print

VERBOSE = False

URL_OPENNEURO = "https://github.com/OpenNeuroDatasets/"
URL_OPENNEURO_DERIVATIVES = "https://github.com/OpenNeuroDerivatives/"


def main():
    datalad_superdataset = Path("/home/remi/datalad/datasets.datalad.org")

    datasets = {
        "name": [],
        "has_participant_tsv": [],
        "has_participant_json": [],
        "participant_columns": [],
        "has_phenotype_dir": [],
        "has_mri": [],
        "nb_subjects": [],
        "raw": [],
        "fmriprep": [],
        "freesurfer": [],
        "mriqc": [],
    }

    datasets = list_openneuro(datalad_superdataset, datasets)

    datasets = pd.DataFrame.from_dict(datasets)

    datasets.to_csv(Path(__file__).resolve().parent / "openneuro.tsv", index=False, sep="\t")

    datasets = {
        "name": [],
        "has_participant_tsv": [],
        "has_participant_json": [],
        "participant_columns": [],
        "has_phenotype_dir": [],
        "has_mri": [],
        "nb_subjects": [],
        "raw": [],
        "fmriprep": [],
        "freesurfer": [],
        "mriqc": [],
    }

    datasets = list_openneuro_derivatives(datalad_superdataset, datasets)

    datasets = pd.DataFrame.from_dict(datasets)

    datasets.to_csv(
        Path(__file__).resolve().parent / "openneuro_derivatives.tsv",
        index=False,
        sep="\t",
    )


def has_mri(bids_pth: Path) -> bool:
    """Return True if at least one subject has at least one MRI modality."""
    return bool(
        list(bids_pth.glob("sub*/func"))
        or list(bids_pth.glob("sub*/ses*/func"))
        or list(bids_pth.glob("sub*/anat"))
        or list(bids_pth.glob("sub*/ses*/anat"))
        or list(bids_pth.glob("sub*/dwi"))
        or list(bids_pth.glob("sub*/ses*/dwi"))
        or list(bids_pth.glob("sub*/perf"))
        or list(bids_pth.glob("sub*/ses*/perf"))
    )


def new_datatset(name: str) -> dict[str, str]:
    return {
        "name": name,
        "has_participant_tsv": "n/a",
        "has_participant_json": "n/a",
        "participant_columns": "n/a",
        "has_phenotype_dir": "n/a",
        "has_mri": "n/a",
        "nb_subjects": "n/a",
        "raw": f"{URL_OPENNEURO}{name}",
        "fmriprep": "n/a",
        "freesurfer": "n/a",
        "mriqc": "n/a",
    }


def list_participants_tsv_columns(participant_tsv: Path) -> list[str]:
    """Return the list of columns in participants.tsv."""
    try:
        df = pd.read_csv(participant_tsv, sep="\t")
        return df.columns.tolist()
    except pd.errors.ParserError:
        warn(f"Could not parse: {participant_tsv}")
        return ["cannot be parsed"]


def list_openneuro(datalad_superdataset: Path, datasets: dict[str, dict[str, str]]):
    openneuro = datalad_superdataset / "openneuro"
    install_dataset(openneuro, verbose=VERBOSE)

    raw_datasets = sorted(list(openneuro.glob("ds*")))

    for dataset_pth in raw_datasets:
        dataset_name = dataset_pth.name
        datatset = new_datatset(dataset_name)
        datatset["nb_subjects"] = get_nb_subjects(dataset_pth)
        datatset["has_mri"] = has_mri(dataset_pth)
        tsv_status, json_status, columns = has_participant_tsv(dataset_pth)
        datatset["has_participant_tsv"] = tsv_status
        datatset["has_participant_json"] = json_status
        datatset["participant_columns"] = columns
        datatset["has_phenotype_dir"] = bool((dataset_pth / "phenotype").exists())

        for der in [
            "fmriprep",
            "freesurfer",
            "mriqc",
        ]:
            if der_datasets := dataset_pth.glob(f"derivatives/*{der}"):
                for i in der_datasets:
                    datatset[der] = f"{URL_OPENNEURO}{dataset_name}/tree/main/derivatives/{i.name}"

        for keys in datasets:
            datasets[keys].append(datatset[keys])

    return datasets


def has_participant_tsv(pth: Path):
    tsv_status = bool((pth / "participants.tsv").exists())
    json_status = bool((pth / "participants.json").exists())
    columns = "n/a"
    if tsv_status:
        columns = list_participants_tsv_columns(pth / "participants.tsv")
    # if json_status:
    #     with open(pth / "participants.json") as f:
    #         json_data = json.load(f)
    #         print(json_data)
    return tsv_status, json_status, columns


def list_openneuro_derivatives(datalad_superdataset: Path, datasets: dict[str, dict[str, str]]):
    """List mriqc datasets and envetually matching fmriprep dataset.

    nb_subjects is the number of subjects in the mriqc dataset.
    """
    openneuro_derivatives = datalad_superdataset / "openneuro-derivatives"

    install_dataset(openneuro_derivatives, verbose=VERBOSE)

    mriqc_datasets = sorted(list(openneuro_derivatives.glob("*mriqc")))

    for dataset_pth in mriqc_datasets:
        dataset_name = dataset_pth.name.replace("-mriqc", "")

        datatset = new_datatset(dataset_name)
        datatset["nb_subjects"] = get_nb_subjects(dataset_pth)
        datatset["has_mri"] = True
        datatset["mriqc"] = f"{URL_OPENNEURO_DERIVATIVES}{dataset_pth.name}"
        tsv_status, json_status, columns = has_participant_tsv(dataset_pth / "sourcedata" / "raw")
        datatset["has_participant_tsv"] = tsv_status
        datatset["has_participant_json"] = json_status
        datatset["participant_columns"] = columns
        datatset["has_phenotype_dir"] = (dataset_pth / "sourcedata" / "raw" / "phenotype").exists()

        fmriprep_dataset = Path(str(dataset_pth).replace("mriqc", "fmriprep"))
        if fmriprep_dataset.exists():
            datatset["fmriprep"] = f"{URL_OPENNEURO_DERIVATIVES}{fmriprep_dataset.name}"

        freesurfer_dataset = fmriprep_dataset / "sourcedata" / "freesurfer"
        if freesurfer_dataset.exists():
            datatset["freesurfer"] = f"{datatset['fmriprep']}/tree/main/sourcedata/freesurfer"

        for keys in datasets:
            datasets[keys].append(datatset[keys])

    fmriprep_datasets = sorted(list(openneuro_derivatives.glob("*fmriprep")))
    for dataset_pth in fmriprep_datasets:
        dataset_name = dataset_pth.name.replace("-fmriprep", "")
        if dataset_name not in datasets["name"]:
            datatset = new_datatset(dataset_name)
            datatset["nb_subjects"] = get_nb_subjects(dataset_pth)
            datatset["has_mri"] = True
            datatset["fmriprep"] = f"{URL_OPENNEURO_DERIVATIVES}{dataset_pth.name}"
            tsv_status, json_status, columns = has_participant_tsv(
                dataset_pth / "sourcedata" / "raw"
            )
            datatset["has_participant_tsv"] = tsv_status
            datatset["has_participant_json"] = json_status
            datatset["participant_columns"] = columns
            datatset["has_phenotype_dir"] = (
                dataset_pth / "sourcedata" / "raw" / "phenotype"
            ).exists()
            freesurfer_dataset = dataset_pth / "sourcedata" / "freesurfer"
            if freesurfer_dataset.exists():
                datatset["freesurfer"] = f"{datatset['fmriprep']}/tree/main/sourcedata/freesurfer"

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


def get_nb_subjects(pth: Path):
    tmp = [v for v in pth.glob("sub-*") if v.is_dir()]
    return len(tmp)


if __name__ == "__main__":
    main()
