#!/bin/bash

#SBATCH --job-name=backup-seq2seq-datasets
#SBATCH --output=joblogs/%x_%j.txt
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --time=00:10:00
#SBATCH --mail-type=END,FAIL,INVALID_DEPEND

git add --all .
git commit -m "add new datasets"
git push origin main