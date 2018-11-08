# NEpy_v0.1
![alt text](./images/screenshots.png)

## Introduction to NEpy
*The simplified version of [NEpy](http://git.starlab.es/Sanchez/NEpy.git "Original NEpy") for Neuroelectrics team.*

This is the repository for *NEpy*, a toolbox to work with [Neuroelectrics](https://www.neuroelectrics.com/ "NE homepage") 
EEG ``.easy`` and ``.easy.gz``(with or without ``.info`` files), or compressed ``.nedf`` files. See the 
[Neuroelectrics wiki](https://www.neuroelectrics.com/wiki/index.php?title=Neuroelectric%27s_Wiki "NE wiki") for more 
information on these file formats.  

The basic class of this repository is ``Frida``, a module to read the data files and provide methods to check the 
quality and perform a basic pre-processing pipeline. NEpy also provides another module called ``batch`` witch uses 
`Frida`'s methods to process *all* the data files in a folder.
*For a detailed information about the modules, please check the 
[Jupyter Notebook Demos](http://git.starlab.es/Sanchez/nepy_support/tree/master/demos " NE jupyter demos"), where you 
can find a description of the module, its main attributes, methods and useful examples of use.*


## Getting started
#### Prerequisites
- NEpy *should* work on the following operating systems: Windows, Mac OS and Linux.  
- It works with Python 3.x
- Size: around 95,0 MB
#### Installation
1. Clone or download the NEpy repository in your computer.  
2. Copy and paste the path where you have saved the repository in a variable
3. Add this path to the Python environment
4. Import nepy

Example:
```
nepypath = 'C:\Users\roser.sanchez\Documents\Git\NEpy_v0.1'

import sys
sys.path.append(nepypath)

import nepy as ne
from nepy.frida.frida import Frida
from nepy.frida.batch import processDirectory
```

Check our [Jupyter Notebook Demos](http://git.starlab.es/Sanchez/nepy_support/tree/master/demos " NE jupyter demos") 
(or .html version) for a great example on how to proper use this module! 

## Contributing
1. Fork it (<https://github.com/sr6033/lterm/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request

![alt text](./images/gitflow.png)

Check the *CONTRIBUTING.md* file for more information.

## Authors
Main: Giulio Ruffini and Roser Sanchez  
Contributors: Sergi Aregall and Javier Acedo.

####Neuroelectrics, November 2018

![alt text](./images/enobio.jpg)