

.. |processArchitecture| image:: https://github.com/amintos/akira/raw/playground/documentation/images/processes_and_communication_final.png
.. |user| image:: https://github.com/amintos/akira/raw/playground/documentation/images/user.png
.. _Process: https://github.com/amintos/akira/blob/playground/process/Process.py
.. _proxy: https://github.com/amintos/akira/blob/playground/process/proxy.py



Processes
=========

Since the application shall be a multiprocess multicomputer application we want to create a basis that makes it easy to program in a distributed way.
After some thoughts: It would be good to have a single object *p* one can carry around anywhere representing a process. 
*p*.call(*function*, *arguments*) then executes the *function* in this process *p* with the given *arguments*.


If one does not have to worry how to connect back to the origins of an object one can more easily implement these:

- Object references to objects in other processes (see reference `(rst)
  <reference.rst>`__ `(html)
  <reference.html>`__ )
- Mobile objects (as Process_ es)


Therefore the following architecture is proposed:


|processArchitecture|


All processes such as Process1 and Process2 have representations as an object.
There is Process1 on the left and Process2 on the right. Both have an object with solid border that represents the process itself.

If now the user |user| in Process1 wants to connect to Process2, it creates a connection to Process2's listener.
This listener then creates a connection on his side of the net for process1.
Process1 in Process2 is a representative for the original Process1 in Process1. It holds the connection.
Both sides of a connection are informed about ther endpoints called fromProcess and toProcess `(rst)
<set_connection_endpoints.rst>`__
`(html)
<set_connection_endpoints.html>`__ .
Process1 in Process1 and Process2 in Process2 are of type Process_.thisProcess.
Process1 in Process2 and Process2 in Process1 are of type Process_.ProcessInOtherProcess.

Questions?
----------

Which processes does my process know? *thisProcess.knownProcesses* 

How does it know about other processes connected? `(rst)
<set_connection_endpoints.rst>`__
`(html)
<set_connection_endpoints.html>`__ .