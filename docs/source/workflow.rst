Workflows
=========

**TODO** *Include a simple definition of workflow*

In *Wok* a workflow is a set of modules that have to be executed in certain order which is determined by the modules interconnections and dependencies. A module represents an intermediate step of processing in the workflow for a set of input data and can generate data that can be input of other modules. Data is interchanged between modules through ports. Each module defines a set of input and output ports that can be interconnected between different modules. The data can be any text message recognized by the connected modules.

XML definition
++++++++++++++

**<flow>**
	This is the root element and represents a workflow definition.

	Attributes:

	- **name**: The workflow identifier.

	Elements:

	- **title**: Title of the workflow.
	- **desc**: Description of the workflow.
	- **in**: Input port. There can be 0 or more elements.
	- **out**: Output port. There can be 0 or more elements.
	- **module**: Module definition. There can be 1 or more elements.

**<in>**
	This element represents an input port.

	Attributes:

	- **name**: The port identifier.
	- **link**: A comma separated list of references to output ports to connect to.

	Elements:

	- **title**: Title of the port.
	- **desc**: Description of the port.

**<out>**
	This element represents an output port. The attributes are the same as *<in>* but without the *link*, and the elements exactly the same.

**<module>**
	This represents a workflow module, an intermediate step of processing.

	Attributes:

	- **name**: The module identifier.
	- **wsize**: This is the desired minimum number of data elements to process per task. It represents the minimum unit of work to guarantee that it won't be wasted more time submitting the task than executing it.
	- **maxpar**: This is the maximum number of partitions allowed for the module. To avoid parallelization of a module put *maxpar="1"* and only one task will be executed.

	Elements:

	- **title**: Title of the module.
	- **desc**: Description of the module.
	- **in**: Input port. There can be 0 or more elements.
	- **out**: Output port. There can be 0 or more elements.
	- **exec**: This tag defines what to execute.

**<exec>**
	This represents the program executed for a module.

	Attributes:

	- **launcher**: The type of program. Possible values: *shell*, *python*, *perl*.

	Elements depending on the launcher selected:

	* **shell**

	* **python**

	* **perl**

