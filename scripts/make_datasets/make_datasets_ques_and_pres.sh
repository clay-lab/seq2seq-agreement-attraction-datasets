#!/bin/bash

#SBATCH --job-name=make-seq2seq-datasets-q
#SBATCH --output=joblogs/%x_%j.txt
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=30GB
#SBATCH --time=10:00:00
#SBATCH --gpus=v100:1
#SBATCH --partition=gpu

module load CUDA
module load cuDNN
module load miniconda

source activate /gpfs/gibbs/project/frank/ref4/conda_envs/seq2seq-datasets

python make_datasets.py -o en_wiki-nodist-ques-and-past
