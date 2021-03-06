# -*- coding: utf-8 -*-
"""
The :mod:`.motif_analysis` module implements transcription factor motif scan.

Genomic activity information (peak of ATAC-seq or Chip-seq) is extracted first.
Then the peak DNA sequence will be subjected to TF motif scan.
Finally we will get list of TFs that potentially binds to a specific gene.

"""

from .motif_analysis_utility import is_genome_installed
from .process_bed_file import peak2fasta, read_bed
from .tfinfo_core import (load_TFinfo, load_TFinfo_from_parquets,
                          make_TFinfo_from_scanned_file, TFinfo, scan_dna_for_motifs,
                          SUPPORTED_REF_GENOME)
from .tss_annotation import get_tss_info
from .process_cicero_data import integrate_tss_peak_with_cicero
from . import process_cicero_data

__all__ = ["is_genome_installed", "peak2fasta", "read_bed", "scan_dna_for_motifs"
           "load_TFinfo", "load_TFinfo_from_parquets",
           "make_TFinfo_from_scanned_file",
           "TFinfo", "SUPPORTED_REF_GENOME",
           "get_tss_info", "process_cicero_data",
           "integrate_tss_peak_with_cicero"]
