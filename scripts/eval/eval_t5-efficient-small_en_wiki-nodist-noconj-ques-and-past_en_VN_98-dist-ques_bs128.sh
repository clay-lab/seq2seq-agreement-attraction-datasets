#!/bin/bash

#SBATCH --job-name=t5-efficient-small-base-eval-tense-en_wiki-nodist-noconj-ques-and-past
#SBATCH --output=joblogs/%x_%j.txt
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=30GB
#SBATCH --time=10:00:00
#SBATCH --gpus=v100:1
#SBATCH --partition=gpu
#SBATCH --mail-type=END,FAIL,INVALID_DEPEND

module load CUDA
module load cuDNN
module load miniconda

source activate /gpfs/gibbs/project/frank/ref4/conda_envs/py38-agratt

python core/run_seq2seq.py \
	--model_name_or_path 't5-efficient-small' \
	--do_learning_curve \
	--task translation_src_to_tgt \
	--train_file data/en_wiki-nodist-noconj-ques-and-past/en_wiki-nodist-noconj-ques-and-past_train.json.gz \
	--validation_file data/en_VN_98-dist-ques/en_VN_98-dist-ques_test.json.gz \
	--output_dir outputs/t5-efficient-small-finetuning-en_wiki-nodist-noconj-ques-and-past-bs128/ \
	--per_device_train_batch_size=8 \
	--per_device_eval_batch_size=16 \
	--overwrite_output_dir \
	--predict_with_generate \
