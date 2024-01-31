# Converts SND@LHC digitised simulation files into input data for ML

The conversion has two parts:
1. SND@LHC digitised ROOT files -> numpy arrays (within SND@LHC experiment software environment)
2. numpy arrays -> pyg format (pytorch + pyg environment, where pyg is a pytorch GNN library)

The two-step procedure is needed because the SND@LHC SW setup does not contain pytorch/pyg.

### SND Digi -> numpy arrays

Main script: [digi_to_ml.py](digi_to_ml.py) runs the conversion based on passed arguments
Condor batch submission: [condor](condor) contains a condor submission files and scripts to create parameter lists and to merge the outputs

### numpy arrays -> pyg format

Main script: [convert_to_pyg.py](preprocessing/convert_to_pyg.py)

