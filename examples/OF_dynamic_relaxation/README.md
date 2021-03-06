# Accelerating CFD solvers

In this test case, we try to check the feasibility of RL to dynamically update underrelaxation factors in CFD solvers to accelerate the convergence in CFD simulations of turbulent flows. We test our framework for the backward facing step examples where an agent is trained for different inlet velocities. The underrelaxation factors for velocity and pressure are updated after every n iterations of CFD simulation.
<p align="center">
	<img src="misc/contour_vectors.png" width="512">
</p>

## Problem formulation

The MDP problem for this test case is formulated as below
- The state of the system is the sum of average value of the square of the velocity at the inlet boundary and in the internal mesh.   
	<p align="center">
		<img src="https://latex.codecogs.com/gif.latex?%5Cdpi%7B150%7D%20s_k%3D%5Cfrac%7B1%7D%7BN_b%7D%5Csum%20U_b%5E2%20&plus;%20%5Cfrac%7B1%7D%7BN_m%7D%5Csum%20U_m%5E2">
	</p>
	
- The agent chooses the underrelaxation factor for discretized momentum and pressure equation.
	<p align="center">
		<img src="https://latex.codecogs.com/gif.latex?%5Cdpi%7B150%7D%20a_k%20%3D%20%5C%7B%5Calpha_u%2C%20%5Calpha_p%20%5C%7D">
	</p>
	
- The reward is the total number of iterations it took for the CFD simulations to converge
	<p align="center">
		<img src="https://latex.codecogs.com/gif.latex?%5Cdpi%7B150%7D%20r_k%20%3D%20n_%7B%5Ctext%7Biter%7D%7D">
	</p>

## Results

- We implemet proxymal policy optimization (PPO) and asynchronous proxymal policy optimization (APPO) for this test case. The PPO agent is trained for 2000 episodes and the APPO agent is trained for 3500 eisodes for different number of workers. 
<p align="center">
	<img src="misc/mean_reward_of.png" width="640">
</p>

- Once the agent is trained, it is tested for three different values of inlet velocities, V = 25.0, 50.0, 75.0 m/s. The boxplot and errorbar plot for the PPO algorithm is shown below.
<p align="center">
	<img src="misc/subplots_of_ppo.png" width="640">
</p>
The boxplot and errorbar plot for the APPO algorithm is shown below.
<p align="center">
	<img src="misc/subplots_of_appo.png" width="640">
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

- For this test case, each CFD simulation is one environment. To collect data from multiple environments for training the RL agent, we need to create multiple instance of the baseCase and run each CFD simulation on different processor. We use the [pyFOAM](https://openfoamwiki.net/index.php/Contrib/PyFoam) library to create multiple instances of the base CFD case. Each case is identified by the `worker_index` which is passed to the environment constructor. 
```
self.worker_index = env_config.worker_index

# make a copy of the baseCase using pyFOAM
self.casename = 'baseCase_'+str(self.worker_index)
orig = SolutionDirectory(origcase,archive=None,paraviewLink=False)
case=orig.cloneCase(self.casename )

```

- The parameters in different dictrionaries in OpenFOAM case can be easily changed with the [pyFOAM](https://openfoamwiki.net/index.php/Contrib/PyFoam) library as follow
```
relax_p, relax_u = action 
        
relaxP = ParsedParameterFile(path.join(self.casename,"system", "fvSolution"))
relaxP["relaxationFactors"]["fields"]["p"] = relax_p
relaxP.writeFile()

relaxU = ParsedParameterFile(path.join(self.casename,"system", "fvSolution"))
relaxU["relaxationFactors"]["equations"]["U"] = relax_u
relaxU.writeFile()
```

- We run the OpenFOAM CFD simulation using the subprocess command. The RLLib handles distribution of running CFD simulation on different processors by itslef.
```
now = strftime("%m.%d.%Y-%H.%M.%S", gmtime())
solverLogFile= f'log.{solver}-{now}'

proc = subprocess.Popen([f'$FOAM_APPBIN/{solver} {solveroptions} {self.casename} >> {self.casename}/{solverLogFile}'],
                        shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
proc.wait()
(stdout, stderr) = proc.communicate()
```

- The residuals from the OpenFOAM log file is extracted into a text file using the bash script `extract_residual.sh` as follow
```
subprocess.run(f'./extract_residual.sh {self.casename}/{solverLogFile} {self.casename} {self.worker_index}',
               shell=True,stderr=subprocess.STDOUT)
```

- The velocity field is extracted using the `foamToVTK` utility and then using [pyVista](https://docs.pyvista.org/) library to read velocity from the genearted VTK files. 
```
import pyvista as vtki
proc = subprocess.Popen([f'$FOAM_APPBIN/foamToVTK {solveroptions} {self.casename} >> {self.casename}/logr.vtkoutput'],
                         shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
proc.wait()
(stdout, stderr) = proc.communicate()

inlet = vtki.PolyData(f'./{self.casename}/VTK/inlet/inlet_{itercount}.vtk')
Ub = inlet.cell_arrays['U']

mesh = vtki.UnstructuredGrid(f'./{self.casename}/VTK/{self.casename}_{itercount}.vtk')
Um = mesh.cell_arrays['U']
```

## Running the code
The job can be submitted on Theta either in the `debug` or `default` mode. Job submission scripts are provided for both `debug` or `default` mode. The user has to specify the project name and RLLib environment in job submission scripts before submitting it. To submit the job in `debug` mode on Theta execute 
```
qsub ray_python_debug.sh
```

## Relevant research articles
[A fuzzy logic algorithm for acceleration of convergence in solving turbulent flow and heat transfer problems](https://www.tandfonline.com/doi/full/10.1080/10407790490487677?casa_token=i_8q5xQgvW8AAAAA%3Ab66y5HtPgflD1Du8xN1jaREaB6EaBC7xMsonk3HJO_qtxGv0csyZGU5nkUXfJlEnykMh9g5WJzMks9w)

