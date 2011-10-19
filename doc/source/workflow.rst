Workflows
=========

**TODO**: *Include a simple definition of workflow*

In *Wok* a workflow is a set of modules that have to be executed in certain order which is determined by the modules interconnections and dependencies. A module represents an intermediate step of processing in the workflow for a set of input data and can generate data that can be input of other modules. Data is interchanged between modules through ports. Each module defines a set of input and output ports that can be interconnected between different modules. The data can be any text message recognized by the connected modules.

XML definition
++++++++++++++

**<flow>**

	This is the root element and represents a workflow definition.

	Attributes:

	- **name**: The workflow identifier.

	Elements:

	- **title**: Title of the workflow. Optional.
	- **desc**: Description of the workflow. Optional.
	- **in**: Input port. There can be 0 or more elements. Optional.
	- **out**: Output port. There can be 0 or more elements. Optional.
	- **module**: Module definition. There can be 1 or more elements.

**<in>**

	This element represents an input port.

	Attributes:

	- **name**: The port identifier.
	- **link**: A comma separated list of references to output ports to connect to.

	Elements:

	- **title**: Title of the port. Optional.
	- **desc**: Description of the port. Optional.

**<out>**

	This element represents an output port. The attributes are the same as *<in>*
	but without the *link*, and the elements exactly the same.

**<module>**

	This represents a workflow module, an intermediate step of processing.

	Attributes:

	- **name**: The module identifier.
	- **wsize**:
		This is the desired minimum number of data elements to process per task.
		It represents the minimum unit of work to guarantee that it won't be wasted
		more time submitting the task than executing it.  Optional. Default 1.
	- **maxpar**:
		This is the maximum number of partitions allowed for the module.
		To avoid parallelization of a module put *maxpar="1"* and only one task will
		be executed.  Optional. Default 0 (no limit)

	Elements:

	- **title**: Title of the module. Optional.
	- **desc**: Description of the module. Optional.
	- **conf**: Allows to specify per module configuration. Optional.
	- **in**: Input port. There can be 0 or more elements. Optional.
	- **out**: Output port. There can be 0 or more elements. Optional.
	- **run**: This tag defines what to execute.

**<conf>**

	The tags inside this tag will be translated to a JSON element and then
	merged with the general configuration before the module starts, so it will
	only affect this module but no others.

	Example::

		<module name="mod1">
			<conf>
				<method>FDR</method>
			</conf>

			<run>correct_pvalues.py</run>
		</module>

**<run>**

	This represents the program executed for a module in order to process the data.
	This program must use the wok framework in order to know which data to process.
	For the time being only	a Python framework exists.

	If the path to the program is relative, then the path of the *.flow* file
	will be used as the base path.

	Attributes:

	- **language**:
		The programming language of the program.
		Possible values: *python*.  Optional. Default: *python*
