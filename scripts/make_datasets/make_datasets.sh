#!/bin/bash

#SBATCH --job-name=make-seq2seq-datasets
#SBATCH --output=joblogs/%x_%j.txt
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=30GB
#SBATCH --time=22:00:00
#SBATCH --gpus=v100:1
#SBATCH --partition=gpu
#SBATCH --mail-type=END,FAIL,INVALID_DEPEND

module load CUDA
module load cuDNN
module load miniconda

source activate /gpfs/gibbs/project/frank/ref4/conda_envs/seq2seq-datasets

python make_datasets.py

git add --all .
git commit -m "added new datasets"
git push origin main
