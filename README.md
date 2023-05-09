# list_openneuro_derivatives

## install

datalad superdataset must be installed via

```bash
datalad install ///
```

openneuro derivatives can be installed via (this will take a while):

```bash
cd datasets.datalad.org
datalad install openneuro-derivatives --recursive -J 12
```

openneuro can be installed via (this will take a while):

```bash
cd datasets.datalad.org
datalad install openneuro --recursive -J 12
```

## listing

run `list_openneuro_dependencies.py` and it will
will create a json file with basic info for each dataset and its derivatives.


## TODO:

- improving checking status of participants.tsv
- make it able to install datasets or subdatasets (especially `sourcedata/raw`) on the fly
- list derivatives datasets on `https://github.com/OpenNeuroDatasets/` and not just
  `https://github.com/OpenNeuroDerivatives/`
