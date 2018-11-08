# NEpy_v0.1

*The simplified version of [NEpy](http://git.starlab.es/Sanchez/NEpy.git "Original NEpy") for Neuroelectrics team.*

This is the repository for **NEpy**, a toolbox to work with [Neuroelectrics](https://www.neuroelectrics.com/ "NE homepage") 
EEG ``.easy`` and ``.easy.gz``(with or without ``.info`` files), or compressed ``.nedf`` files. See the 
[Neuroelectrics wiki](https://www.neuroelectrics.com/wiki/index.php?title=Neuroelectric%27s_Wiki "NE wiki") for more 
information on these file formats.  

The basic class of this repository is ``Frida``, a module to read the data files and provide methods to check the 
quality and perform a basic pre-processing pipeline. NEpy also provides another module called ``batch`` witch uses 
`Frida`'s methods to process *all* the data files in a folder.
**For a detailed information about the modules, please check the 
[Jupyter Notebook Demos](http://git.starlab.es/Sanchez/nepy_support/tree/master/demos " NE jupyter demos"), where you 
can find a description of the module, its main attributes, methods and useful examples of use.**

