#!/bin/bash
#SBATCH --job-name=dataset_build
#SBATCH --time=00:30:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=2
#SBATCH --output=logs/datasetbuild_%j.out
#SBATCH --error=logs/datasetbuild_%j.err

cd /mnt/appbio_a/groups/Year_4/EAgnanti/variant_project
python src/build_dataset.py
