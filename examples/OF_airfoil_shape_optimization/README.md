# Shape optimization
In this test case, we use single step PPO algorithm to optimize aerodynamic shape. The framework is developed for shape optimization of NACA 0012 airfoil with an objective to maximize lift to drag ratio. 

## To do: Validate CFD model with experimental data 

## Problem formulation
The MDP problem for this test case is formulated as below
- The airfoil shape is parameterized using the bezier cure with 6 control points. There are total 13 control parameters which includes the x and y co-ordinates of 6 control points and the leading edge radius. The action at each time step is the selection of 13 control points. 
	<p align="center">
		<img src="https://latex.codecogs.com/gif.latex?%5Cdpi%7B150%7D%20a_k%3D%7Bc_%7B1x%7D%2Cc_%7B1y%7D%2C%5Cdots%2Cc_%7B6x%7D%2Cc_%7B6y%7D%2Cr%7D">
	</p>

- The inlet velocity is used as the state of the system. Since, each episode is comprised of only one time step, the agent sees the same state throughout the training. 
	<p align="center">
		<img src="https://latex.codecogs.com/gif.latex?%5Cdpi%7B150%7D%20s_k%3DV">
	</p>

- The reward is computed as the ratio of lift coefficient to the drag coefficient. The constraint such as constant lift coefficient can be taken into account by adding a penalty function to the reward function.
	<p align="center">
		<img src="https://latex.codecogs.com/gif.latex?%5Cdpi%7B150%7D%20r_k%3D%5Cfrac%7BC_L%7D%7BC_D%7D">
	</p>

## Results
- The agent is trained using the PPO agorithm for 3000 episodes. The histroy of instantaneous, moving average maximum, and moving average mean reward is shown in the below Figure.
	<p align="center">
		<img src="misc/reward.png" width="640">
	</p>

- There Figure below shows the shape of original NACA 0012 airfoil and optimizes airfoil along with control points for each geometry.
	<p align="center">
		<img src="misc/parameterized_rl.png" width="640">
	</p>

## Running OpenFoam with RLLib

- The OpenFOAM case is setup using a set of files that contains the information about mesh, boundary conditions, solver, turbulent model properties, etc. The basic directory structure of OpenFOAM case is described below
```
.
baseCase
├── system
│   ├── controlDict
│   ├── fvSchemes
│   ├── fvSolution
│   └── blockMeshDict
├── constant
│   ├── polyMesh
│   ├── transportProperties
│   └── turbulenceProperties
└── time directories
```

- The *blockMeshDict* file in the *system* folder contains the mesh details. At each time step new airfoil shape needs to be generated and hence the `blockMeshDict` file needs to be updated for each time step. We use *blockMeshDictGenerator.xlsx* file to generate *blockMeshDict* file by specifying the coordinates of an airfoil in its input sheet (The details of blockMeshDictGenerator.xlsx sheet can be found [here](https://www.phanquocthien.org/mesh-geometry/blockmesh/airfoil)). We use data frame in pandas to copy data from exel sheet to the *blockMeshDict*. Once the *blockMeshDict* file is copied in the *system* folder, meshing can be done with subprocess as follow 

```
mesh = 'blockMesh'
now = strftime("%m.%d.%Y-%H.%M.%S", gmtime())
meshLogFile= f'log.{mesh}-{now}'
     
proc = subprocess.Popen([f'$FOAM_APPBIN/{mesh} {solveroptions} {self.casename} >> {self.casename}/{meshLogFile}'],
                        shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)        
proc.wait()
(stdout, stderr) = proc.communicate()
```

- We utilize run-time data processing utilities of OpenFOAM to get the lift and drag coefficient. Specifically, we use *forceCoeffsIncompressible* utility in OpenFOAM, which writes the lift and drag coefficient data in the *postProcessing* folder.


## Running the code
The job can be submitted on Theta either in the `debug` or `default` mode. Job submission scripts are provided for both `debug` or `default` mode. The user has to specify the project name and RLLib environment in job submission scripts before submitting it. To submit the job in `debug` mode on Theta execute 
```
qsub ray_python_debug.sh
```

## Relevant research articles
[Direct shape optimization through deep reinforcement learning](https://arxiv.org/abs/1908.09885)

[Optimization and passive flow control using single-step deep reinforcement learning](https://arxiv.org/abs/2006.02979)

