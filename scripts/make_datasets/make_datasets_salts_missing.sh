#!/bin/bash

#SBATCH --job-name=make-datasets-salts-missing
#SBATCH --output=joblogs/%x_%j.txt
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=30GB
#SBATCH --time=04-00:00:00
#SBATCH --partition=week

module load CUDA
module load cuDNN
module load miniconda

source activate /gpfs/gibbs/project/frank/ref4/conda_envs/seq2seq-datasets

python make_datasets.py -o en_wiki-salts-missing
