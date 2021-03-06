.. _install:

Installation
============

``celloracle`` uses several python libraries and R library. Please follow this guide below to install the dependent software of celloracle.

.. _require:

Docker image
------------

- Not available now. Comming soon.

System Requirements
--------------------

- Operating system: macOS or linux are highly recommended. ``celloracle`` was developed and tested in Linux and macOS.
- We found that the celloracle calculation may be EXTREMELY SLOW under an environment of Windows Subsystem for Linux (WSL). We do not recommend using WSL.
- While you can install ``celloracle`` in Windows OS, please do so at your own risk and responsibility. We DO NOT provide any support for the use in the Windows OS.

- Memory: 8 G byte or more.  Memory usage also depends on your scRNA-seq data. Especially in silico perturbation requires large amount of memory.
- CPU: Core i5 or better processor. GRN inference supports multicore calculation. Higer number of CPU cores enables faster calculation.


Python Requirements
-------------------

- ``celloracle`` was developed with python 3.6. We do not support python 2.7x or python <=3.5.
- Please install all dependent libraries before installing ``celloracle`` according to the instructions below.
- ``celloracle``  is still beta version and it is not available through PyPI or anaconda distribution yet. Please install ``celloracle`` from GitHub repository according to the instruction below.


0. (Optional) Make a new environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This step is optional. Please make a new python environment for celloracle and install dependent libraries in it if you get some software conflicts.

::

    conda create -n celloracle_env python=3.6
    conda activate celloracle_env



1. Add conda channels
^^^^^^^^^^^^^^^^^^^^^
Installation of some libraries requires non-default anaconda channels. Please add the channels below. Instead, you can explicitly enter the channel when you install a library.

::

    conda config --add channels defaults
    conda config --add channels bioconda
    conda config --add channels conda-forge


2. Install `velocyto <http://velocyto.org/velocyto.py/install/index.html>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Please install velocyto with the following commands or `the author's instruction <http://velocyto.org/velocyto.py/install/index.html>`_ .
On Mac OS, you may have a compile error during velocyto installation. I recommend installing `Xcode <https://developer.apple.com/xcode/>`_ in that case.


::

    conda install numpy scipy cython numba matplotlib scikit-learn h5py click

Then

::

    pip install velocyto

3. Install `scanpy <https://scanpy.readthedocs.io/en/stable/installation.html>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Please install scanpy with the following commands or `the author's instruction <https://scanpy.readthedocs.io/en/stable/installation.html>`_ .

::

    conda install seaborn statsmodels numba pytables python-igraph louvain

Then

::

    pip install scanpy

4. Install `gimmemotifs <https://gimmemotifs.readthedocs.io/en/master/installation.html>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Please install gimmemotifs with the following commands or `the author's instruction <https://gimmemotifs.readthedocs.io/en/master/installation.html>`_ .


::

    conda install gimmemotifs genomepy=0.5.5


5. Install other python libraries
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Please install other python libraries below with the following commands.

::

    conda install goatools pyarrow tqdm joblib jupyter


6. install celloracle from github
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

    pip install git+https://github.com/morris-lab/CellOracle.git



R requirements
--------------

``celloracle`` use R libraries for the network analysis and scATAC-seq analysis.
Please install `R <https://www.r-project.org>`_ (>=3.5) and R libraries below according to the author's instruction.

`Seurat <https://satijalab.org/seurat/install.html>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Please install ``Seurat`` with the following r-script or `the author's instruction <https://satijalab.org/seurat/install.html>`_ .
``celloracle`` is compatible with both Seurat V2 and V3.
If you use only ``scanpy`` for the scRNA-seq preprocessing and do not use ``Seurat`` , you can skip installation of ``Seurat``.

In R console,

.. code-block:: r

   install.packages('Seurat')

`Cicero <https://cole-trapnell-lab.github.io/cicero-release/docs/#installing-cicero>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Please install ``Cicero`` with the following r-script or `the author's instruction <https://cole-trapnell-lab.github.io/cicero-release/docs/#installing-cicero>`_ .
If you do not have scATAC-seq data and plan to use celloracle's base GRN, you do not need to install ``Cicero``.

In R console,

.. code-block:: r

   if (!requireNamespace("BiocManager", quietly = TRUE))
   install.packages("BiocManager")
   BiocManager::install("cicero")

`igraph <https://igraph.org/r/>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Please install ``igraph`` with the following r-script or `the author's instruction <https://igraph.org/r/>`_ .

In R console,

.. code-block:: r

   install.packages("igraph")


`linkcomm <https://cran.r-project.org/web/packages/linkcomm/index.html>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Please install ``linkcomm`` with the following r-script or `the author's instruction <https://cran.r-project.org/web/packages/linkcomm/index.html>`_ .

In R console,

.. code-block:: r

   install.packages("linkcomm")

`rnetcarto <https://github.com/cran/rnetcarto/blob/master/src/rgraph/README.md>`_
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Please install ``rnetcarto`` with the following r-script or `the author's instruction <https://github.com/cran/rnetcarto/blob/master/src/rgraph/README.md>`_ .

In R console,

.. code-block:: r

   install.packages("rnetcarto")



Check installation
^^^^^^^^^^^^^^^^^^
These R libraries above are necessary for the network analysis in celloracle. You can check installation using celloracle's function.

In python console,

.. code-block:: Python

   import celloracle as co
   co.network_analysis.test_R_libraries_installation()

Please make sure that all R libraries are installed. The following message will be shown when all R libraries are appropriately installed.

| checking R library installation: igraph -> OK
| checking R library installation: linkcomm -> OK
| checking R library installation: rnetcarto -> OK
