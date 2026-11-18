# FeminicideNewsData

**Dataset, scraping pipelines, and graph-based analysis of femicide news coverage through a Data Feminism framework. Code and data accompanying our *Frontiers* manuscript.**

---

## Overview & Purpose

This repository contains the source code, data processing workflows, and curated datasets used in our study submitted to *Frontiers* regarding the media portrayal of femicides. Drawing on the core principles of **Data Feminism** (D'Ignazio & Klein), this project audits how digital news outlets narrate, classify, and often invisibilize or revictimize gender-based killings.

Official institutional records on femicides frequently suffer from underreporting, delays, or structural fragmentation. While digital media serves as an alternative monitoring source, journalistic narratives often embed systemic biases—such as framing gender violence as "crimes of passion," victim-blaming, or omitting broader structural contexts. This codebase serves as the main data source for the paper's graph-based investigation.

## Repository Structure

- `/FirstRun`: Primary extracted (`noticias_extraidas`) and cleaned/curated (`noticias_limpias_finales`) news datasets.
- `/src` *(or root scripts)*: Web scraping pipelines for digital press collection, data preprocessing, and graph construction/network analysis scripts to model narrative patterns and structural relationships in media coverage.
- `captura_rapida*`: Raw rapid-capture news datasets from media monitoring runs.

## Dataset Reconstruction Instructions

Due to GitHub's 100 MB individual file size limit, the compressed JSON datasets (`.zip`) have been split into 90 MB chunks (`.part1`, `.part2`, `.part3`). To reconstruct the original datasets locally after cloning the repository, run the corresponding command for your operating system:

### Windows (PowerShell / CMD)
Navigate to the folder containing the split files (e.g., `FirstRun/`) and run:
```powershell
cmd /c copy /b noticias_limpias_finales.zip.part* noticias_limpias_finales.zip
cmd /c copy /b noticias_extraidas.zip.part* noticias_extraidas.zip
