# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

"""with open('requirements.txt') as f:
    requirements = f.read()
"""
setup(
    name='celloracle',
    version='0.3.0',
    description='GRN analysis with single cell data',
    long_description=readme,
    python_requires='>=3.6',
    classifiers=[# How mature is this project? Common values are
                #   3 - Alpha
                #   4 - Beta
                #   5 - Production/Stable
                'Development Status :: 4 - Beta',

                # Indicate who your project is intended for
                'Intended Audience :: Developers',
                'Topic :: Software Development :: Build Tools',

                # Pick your license as you wish (should match "license" above)
                # 'License :: OSI Approved :: MIT License',

                # Specify the Python versions you support here. In particular, ensure
                # that you indicate whether you support Python 2, Python 3 or both.
                'Programming Language :: Python :: 3.6',
                'Programming Language :: Python :: 3.7'
            ],
    install_requires=['numpy',
                      'scipy',
                      'cython',
                      'numba',
                      'matplotlib',
                      'seaborn',
                      'scikit-learn',
                      'h5py',
                      'pandas',
                      'velocyto>=0.17',
                      'pyarrow',
                      'jupyter',
                      'tqdm',
                      "python-igraph",
                      "louvain",
                      "fa2",
                      'scanpy',
                      'joblib',
                      'goatools',
                      'genomepy==0.5.5',
                      'gimmemotifs>=0.13.1'],
    author='Kenji Kamimoto at Samantha Morris Lab',
    author_email='kamimoto@wustl.edu',
    url='https://github.com/morris-lab/CellOracle',
    license=license,
    package_data={"celloracle": ["go_analysis/data/*.txt", "go_analysis/data/*.obo",
                                 "data_conversion/*.R",
                                 "motif_analysis/tss_ref_data/*.bed",
                                 "data/TFinfo_data/*.txt", "data/TFinfo_data/*.parquet",
                                 "network_analysis/rscripts_for_network_analysis/*.R"]},
    packages=["celloracle", "celloracle.data_conversion", "celloracle.network", "celloracle.trajectory",
              "celloracle.data", "celloracle.go_analysis",
              "celloracle.motif_analysis", "celloracle.network_analysis", "celloracle.utility"],
    entry_points={'console_scripts':['seuratToAnndata = celloracle.data_conversion.process_srurat_object:main']}

)
