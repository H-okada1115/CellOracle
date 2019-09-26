# -*- coding: utf-8 -*-
'''
This file contains custom functions for the analysis of ATAC-seq data.
Genomic activity information (peak of ATAC-seq) will be extracted first.
Then the peak DNA sequence will be subjected to TF motif scan.
Finally we will get list of TFs that potentially binds to a specific gene.

Codes were written by Kenji Kamimoto.


'''

###########################
### 0. Import libralies ###
###########################


# 0.1. libraries for fundamental data science and data processing

import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
#import seaborn as sns

import sys
import os
import pickle
import glob
import logging
from copy import deepcopy
from datetime import datetime

from tqdm import tqdm_notebook as tqdm

from genomepy import Genome

from gimmemotifs.motif import default_motifs
from gimmemotifs.scanner import Scanner

from ..utility.hdf5_processing import dump_hdf5, load_hdf5
from ..utility import save_as_pickled_object, load_pickled_object, intersect,\
                      makelog, inverse_dictionary
#
from .motif_analysis_utility import scan_dna_for_motifs, is_genome_installed
from .process_bed_file import read_bed, peak2fasta

SUPPORTED_REF_GENOME = {"Human": ['hg38', 'hg19', 'hg18', 'hg17', 'hg16'],
                        "Mouse": ['mm10', 'mm9', 'mm8', 'mm7', 'micMur2', 'micMur1']}


def load_TFinfo(file_path):
    """
    Load TFinfo object which was saved as hdf5 file.

    Args:
        file_path (str): file path.

    Returns:
        TFinfo: Loaded TFinfo object.

    """
    return load_hdf5(filename=file_path, obj_class=TFinfo)

def load_TFinfo_from_parquets(folder_path):
    """
    Load TFinfo object which was saved with the function; "save_as_parquet".

    Args:
        folder_path (str): folder path

    Returns:
        TFinfo: Loaded TFinfo object.
    """

    folder_path_ = os.path.abspath(os.path.join(folder_path, "TFinfo_comp"))
    tfi = load_pickled_object(os.path.join(folder_path_, "tfi.pickle"))

    compressed_files_path = glob.glob(os.path.join(folder_path_, "*.parquet"))
    compressed_file_name = [i.split("/")[-1] for i in  compressed_files_path]

    for name, path in zip(compressed_file_name, compressed_files_path):
        if name == "scanned_df.parquet":
            tfi.scanned_df = pd.read_parquet(path)
        if name == "peak_df.parquet":
            tfi.peak_df = pd.read_parquet(path)
        if name == "TF_onehot.parquet":
            tfi.TF_onehot = pd.read_parquet(path)
    return tfi

def make_TFinfo_from_scanned_file(path_to_raw_bed, path_to_scanned_result_bed, ref_genome):
    """
    This function is currently an available.

    """


    peak_df = read_bed(path_to_raw_bed)
    peak_df = peak_df.drop(columns=["chrom", "start", "end"],axis=1)
    peak_df = peak_df.rename(columns={"name":"gene_short_name",
                                      "seqname":"peak_id"})

    tfinfo = TFinfo(peak_data_frame=peak_df, ref_genome=ref_genome)


    tfinfo.all_target_gene = tfinfo.peak_df.gene_short_name.unique()
    tfinfo.all_peaks = tfinfo.peak_df.peak_id.unique()

    tfinfo.scanned_df = read_bed(path_to_scanned_result_bed).rename(columns={"name": "motif_id"})


    return tfinfo



class TFinfo():
    """
    This is a custom class for motif analysis in celloracle.
    TFinfo object performs motif scan using the TF motif database in gimmemotifs and several functions of genomepy.
    Analysis results can be exported as a python dictionary or dataframe.
    These files; python dictionary of dataframe of TF binding information, are needed in GRN inference.

    Attributes:
        peak_df (pandas.dataframe): dataframe about DNA peak and target gene data.
        all_target_gene (array of str): target genes.
        ref_genome (str): reference genome name that was used in DNA peak generation.
        scanned_df (dictionary): Results of motif scan. Key is a peak name. Value is a dataframe of motif scan.
        dic_targetgene2TFs (dictionary): Final product of Motif scan. Key is a target gene. Value is a list of regulatory candidate genes.
        dic_peak2Targetgene (dictionary): Dictionary. Key is a peak name. Value is a list of the target gene.
        dic_TF2targetgenes (dictionary): Final product of Motif scan. Key is a TF. Value is a list of potential target genes of the TF.

    """

    def __init__(self, peak_data_frame, ref_genome):
        """
        Instantiate TFinfo object.

        Args:
           peak_data_frame (pandas.dataframe): dataframe about DNA peak and target gene data.

           ref_genome (str): reference genome name that was used in DNA peak generation.

        """


        self.easy_log = pd.DataFrame()
        self.__addLog("initiation")

        self.peak_df = peak_data_frame.copy()
        # remove redundant information and check column name
        self.peak_df = self.peak_df.groupby(["peak_id","gene_short_name"]).sum()
        self.peak_df = self.peak_df.reset_index(drop=False)


        self.all_target_gene = self.peak_df.gene_short_name.unique()
        self.all_peaks = self.peak_df.peak_id.unique()

        self.ref_genome = ref_genome

        # check ref_genome is supported or not
        if ref_genome in SUPPORTED_REF_GENOME["Mouse"]:
            self.species = "Mouse"
        elif ref_genome in SUPPORTED_REF_GENOME["Human"]:
            self.species = "Human"
        else:
            raise ValueError(f"ref_genome: {ref_genome} is not supported in celloracle. See celloracle.motif_analysis.SUPPORTED_REF_GENOME to get supported ref genome list.")

        # check  genome installation
        if not is_genome_installed(ref_genome=ref_genome):
            raise ValueError(f"ref_genome: {ref_genome} is not installed. TFinfo initiation failed.")

        self.dic_motif2TFs = _get_dic_motif2TFs(species=self.species)

        self.scanned_df = None
        self.TF_onehot = None
        self.scanned_filtered = None
        self.index_to_be_used = None
        self.thresholding_comment = []


    def __addLog(self, info):

        new_df = pd.DataFrame({"time": [datetime.now().ctime()], "info": [info]})
        self.easy_log = pd.concat([self.easy_log, new_df], axis=0).reset_index(drop=True)

    def copy(self):
        """
        Deepcoty itself.
        """
        return deepcopy(self)


    def save_as_parquet(self, folder_path=None):
        """
        Save itself. Some attributes are saved as parquet file.

        Args:
            folder_path (str): folder path
        """

        os.makedirs(folder_path, exist_ok=True)

        tmp_self = self.copy()

        tmp_self.peak_df.to_parquet(os.path.join(folder_path, "peak_df.parquet"))
        tmp_self.peak_df = None

        if not self.scanned_df is None:
            tmp_self.scanned_df.to_parquet(os.path.join(folder_path, "scanned_df.parquet"))
            tmp_self.scanned_df = None

        if not self.TF_onehot is None:
            tmp_self.TF_onehot.to_parquet(os.path.join(folder_path, "TF_onehot.parquet"))
            tmp_self.TF_onehot = None

        self.__addLog("save_as_compressed")

        save_as_pickled_object(tmp_self, os.path.join(folder_path, "tfi.pickle"))

        print(f"file saved in: {folder_path}")


    def to_hdf5(self, file_path):
        """
        Save object as hdf5.

        Args:
            file_path (str): file path to save file. Filename needs to end with '.celloracle.tfinfo'
        """
        if file_path.endswith(".celloracle.tfinfo"):
            pass
        else:
            raise ValueError("Filename needs to end with '.celloracle.tfinfo'")

        compression_opts = 7
        dump_hdf5(obj=self, filename=file_path,
                  data_compression=compression_opts,  chunks=(2048, 2048),
                  noarray_compression=compression_opts, pickle_protocol=2)



    def scan(self, background_length=200, fpr=0.02, n_cpus=-1, verbose=True):
        """
        Scan DNA sequences searching for TF binding motifs.

        Args:
           background_length (int): background length. This is used for the calculation of the binding score.

           fpr (float): False positive rate for motif identification.

           n_cpus (int): number of CPUs for parallel calculation.

           verbose (bool): Whether to show a progress bar.

        """


        self.fpr = fpr
        self.background_length = background_length
        print("initiating scanner ...")
        ## 1. initialilze scanner  ##
        # load motif
        motifs = default_motifs()

        # initialize scanner
        s = Scanner(ncpus=n_cpus)

        # set parameters
        s.set_motifs(motifs)
        s.set_background(genome=self.ref_genome, length=background_length)
        #s.set_background(genome="mm9", length=400)
        s.set_threshold(fpr=fpr)

        ## 2. motif scan ##
        print("getting DNA sequences ...")
        target_sequences = peak2fasta(self.all_peaks, self.ref_genome)
        print("scanning motifs ...")
        self.scanned_df = scan_dna_for_motifs(s, motifs, target_sequences, verbose)

        self.__addLog("scanMotifs")

    def reset_dictionary_and_df(self):
        """
        Reset TF dictionary and TF dataframe.
        The following attributes will be erased; TF_onehot, dic_targetgene2TFs, dic_peak2Targetgene, dic_TF2targetgenes.

        """
        self.TF_onehot = None
        self.dic_targetgene2TFs = None
        self.dic_peak2Targetgene = None
        self.dic_TF2targetgenes = None

    def reset_filtering(self):
        """
        Reset filtering information.
        You can use this function to stat over the filtering step with new conditions.
        The following attributes will be erased; TF_onehot, dic_targetgene2TFs, dic_peak2Targetgene, dic_TF2targetgenes.

        """
        self.scanned_filtered = None
        self.reset_dictionary_and_df()

    def filter_peaks(self, peaks_to_be_remained):
        """
        Filter peaks.

        Args:
            peaks_to_be_remained (array of str): list of peaks. Peaks that are NOT in the list will be removed.

        """
        if self.scanned_df is None:
            raise ValueError("Motif Scan is not done.")

        if self.scanned_filtered is None:
            self.scanned_filtered = self.scanned_df[["seqname", "motif_id", "score"]].copy()

        before = len(self.scanned_filtered)
        self.scanned_filtered = self.scanned_filtered[self.scanned_filtered.seqname.isin(peaks)]
        after = len(self.scanned_filtered)
        print(f"peaks were filtered: {before} -> {after}")

        self.reset_dictionary_and_df()

        self.thresholding_comment.append(f"threshold peaks")
        self.__addLog("setThresholding_byBindScore")

    def filter_motifs_by_score(self, threshold, method="cumlative_score"):
        """
        Remove motifs with low binding scores.

        Args:
            method (str): thresholding method. Select either of ["indivisual_score", "cumlative_score"]
        """
        if method == "cumlative_score":
            self._thresholding_by_cumlative_bind_score(threshold_score=threshold)

        elif method == "indivisual_score":
            self._thresholding_by_bind_score(threshold_score=threshold)

        else:
            raise ValueError("Method is wrong. Select from ['indivisual_score', 'cumlative_score'] ")


    def _thresholding_by_bind_score(self, threshold_score):
        if self.scanned_df is None:
            raise ValueError("Motif Scan is not done.")

        if self.scanned_filtered is None:
            self.scanned_filtered = self.scanned_df[["seqname", "motif_id", "score"]].copy()

        before = len(self.scanned_filtered)
        self.scanned_filtered = self.scanned_filtered[self.scanned_filtered.score>=threshold_score]
        after = len(self.scanned_filtered)
        print(f"peaks were filtered: {before} -> {after}")

        self.reset_dictionary_and_df()

        self.thresholding_comment.append(f"score_threshold:_{threshold_score}")
        self.__addLog("thresholdingByBindScore")


    def _thresholding_by_cumlative_bind_score(self, threshold_score):
        if self.scanned_df is None:
            raise ValueError("Motif Scan is not done.")

        if self.scanned_filtered is None:
            self.scanned_filtered = self.scanned_df[["seqname", "motif_id", "score"]].copy()

        before = len(self.scanned_filtered)

        tmp = self.scanned_filtered.groupby(by=["seqname", "motif_id"]).sum()
        tmp = tmp[tmp.score >= threshold_score]
        tmp = tmp.reset_index()
        self.scanned_filtered = tmp

        self.reset_dictionary_and_df()

        after = len(self.scanned_filtered)
        print(f"peaks were filtered: {before} -> {after}")
        self.__addLog("thresholdingByAcumulatedBindScore")

    def make_TFinfo_dataframe_and_dictionary(self, verbose=True):
        """
        This is the final step of motif_analysis.
        Convert scanned results into a data frame and dictionaries.

        Args:
            verbose (bool): Whether to show a progress bar.
        """
        if self.scanned_filtered is None:
            self.scanned_filtered = self.scanned_df[["seqname", "motif_id", "score"]].copy()

        if verbose:
            print("1. converting scanned results into one-hot encoded dataframe.")
        self._make_TFinfo_dataframe(verbose=verbose)

        if verbose:
            print("2. converting results into dictionaries.")
            self._make_dictionaries(verbose=verbose)

    def _make_TFinfo_dataframe(self, verbose=True):
        """
        Convert scanned results into one-hot encoded dataframe.
        rows are peak index, columns are TFs.
        The value is 1 If TF have binding motif in the peak.
        The result will stored in self.TF_onehot

        Args:
            verbose (bool): Whether to show progressbar.

        """

        def _motifs_to_TFs_as_onehot_series(motifs):

            tfs = []
            for motif in motifs:
                tfs += self.dic_motif2TFs[motif]

            tfs = np.unique(tfs)

            series = pd.Series(np.repeat(1, len(tfs)), index=tfs)
            return series


        # preprocess
        peak_list = self.scanned_filtered.seqname.unique()
        multi_index_df = self.scanned_filtered.set_index(["seqname", "motif_id"])

        # process data
        li = []
        if verbose:
            loop = tqdm(peak_list)
        else:
            loop = peak_list
        for peak in loop:
            motifs = multi_index_df.loc[peak].index.values
            series = _motifs_to_TFs_as_onehot_series(motifs)
            li.append(series)

        # get hot encoded Data frame
        self.TF_onehot = pd.concat(li, axis=1, sort=True).transpose()
        del li

        self.TF_onehot = self.TF_onehot.fillna(0).astype("int")
        self.TF_onehot.index = peak_list

        self.__addLog("makeOnehotDataframe")

    def _make_dictionaries(self, verbose=True):
        """
        Convert scanned results into dictionaries.

        The result will stored in self.dic_targetgene2TFs and self.dic_TF2targetgenes

        self.dic_TF2targetgene

        Args:
            verbose (bool): Whether to show progressbar.

        """
        if self.TF_onehot is None:
            raise ValueError("Process has not complete yet.")

        if verbose:
            print("converting scan results into dictionaries...")

        dic_targetgene2TFs ={}
        dic_peak2Targetgene = {}

        if verbose:
            loop = tqdm(self.all_target_gene)
        else:
            loop = self.all_target_gene
        for tg in loop:
            peaks = self.peak_df[self.peak_df.gene_short_name==tg].peak_id.values
            peaks = np.array(intersect(peaks, self.TF_onehot.index))
            #print(peaks)

            tmp_series = self.TF_onehot.loc[peaks].max(axis=0)
            tfs = tmp_series[tmp_series==1].index.values
            dic_targetgene2TFs[tg] = tfs

            for peak in peaks:
                dic_peak2Targetgene[peak] = tg



        self.dic_targetgene2TFs = dic_targetgene2TFs
        self.dic_peak2Targetgene = dic_peak2Targetgene

        self.dic_TF2targetgenes = inverse_dictionary(dictionary=dic_targetgene2TFs,
                                                     verbose=verbose,
                                                     return_value_as_numpy=True)

        self.__addLog("make_dictionaries")


    def to_dataframe(self, verbose=True):
        """
        Return results as a dataframe.
        Rows are peak_id, and columns are TFs.

        Args:
            verbose (bool): Whether to show a progress bar.

        Returns:
            pandas.dataframe: TFinfo matrix.
        """
        if self.TF_onehot is None:
            if verbose:
                print("Converting scanned results into one-hot encoded dataframe ...")
            self._make_TFinfo_dataframe(verbose=verbose)

        tmp_peak_df = self.TF_onehot.reindex(self.peak_df.peak_id.values).fillna(0)
        tmp_peak_df = tmp_peak_df.reset_index(drop=True)

        tmp = pd.concat([self.peak_df, tmp_peak_df], axis=1)


        return tmp



    def to_dictionary(self, dictionary_type="targetgene2TFs", verbose=True):
        """
        Return TF information as a python dictionary.

        Args:
            dictionary_type (str): Type of dictionary. Select from ["targetgene2TFs", "TF2targetgenes"].
                If you chose "targetgene2TFs", it returns a dictionary in which a key is a target gene, and a value is a list of regulatory candidate genes (TFs) of the target.
                If you chose "TF2targetgenes", it returns a dictionary in which a key is a TF and a value is a list of potential target genes of the TF.
        Returns:
            dictionary: dictionary.
        """
        if self.TF_onehot is None:
            self.make_TFinfo_dataframe_and_dictionary(verbose=verbose)

        elif (self.dic_targetgene2TFs is None) | (self.dic_TF2targetgenes is None):
            if verbose:
                print("Converting results into dictionaries.")
            self.make_dictionaries(verbose=verbose)

        if dictionary_type == "targetgene2TFs":
            return self.dic_targetgene2TFs

        elif dictionary_type == "TF2targetgenes":
            return self.dic_TF2targetgenes

        else:
            raise ValueError(f'{dictionary_type} is not available for dictionary_type.\nSelect from ["targetgene2TFs", "TF2targetgenes"]')




######################################################
### 4.2. Make TFinfo dataFrame for GRN inference  ###
######################################################



def _get_dic_motif2TFs(species):

    motifs  = default_motifs()
    motif_names = [i.id for i in motifs]
    factors_direct = [i.factors["direct"] for i in motifs]
    factors_indirect = [i.factors["indirect"] for i in motifs]

    dic_motif2TFs = {}
    if species == "Mouse":
        for i in motifs:
            fcs = i.factors["direct"] + i.factors["indirect"]
            dic_motif2TFs[i.id] = [fa.capitalize() for fa in fcs]
    if species == "Human":
        for i in motifs:
            fcs = i.factors["direct"] + i.factors["indirect"]
            dic_motif2TFs[i.id] = [fa.upper() for fa in fcs]

    return dic_motif2TFs




#########################################################
### 4.2. Calculate P-values; Multi processing version ###
#########################################################



#########################
### 5.1 Visualization ###
#########################




######################
### 6. GO analysis ###
######################


#############################
### Scoring with ML model ###
#############################