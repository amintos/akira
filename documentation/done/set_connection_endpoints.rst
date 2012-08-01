
.. |user| image:: https://github.com/amintos/akira/raw/playground/model/images/user.png




How does a connection know about its endpoints?
-----------------------------------------------

The user |user| wants to connect to Process2.


.. image:: https://raw.github.com/amintos/akira/playground/model/images/connection_endpoints_1.png

So the user creates a connection to a listener of Process2.

.. image:: https://raw.github.com/amintos/akira/playground/model/images/connection_endpoints_2.png

The listener creates a connection object on the other side, in Process2.

.. image:: https://raw.github.com/amintos/akira/playground/model/images/connection_endpoints_3.png

Both connections know where they are from. But they do not know where they lead to. 

.. image:: https://raw.github.com/amintos/akira/playground/model/images/connection_endpoints_4.png

So the Process2, the side of the listener, starts sending commands to the other side of the connection. Process2 in Process1 comes out as a representative of the original Process2 in Process2.

Connection in Process1 leads to process Process2.

.. image:: https://raw.github.com/amintos/akira/playground/model/images/connection_endpoints_5.png

After that the other way around.. a representative of Process1 is created in Process2.

.. image:: https://raw.github.com/amintos/akira/playground/model/images/connection_endpoints_6.png

This would go on as a loop but luckily it can be interrupted if toProcess is already set.

.. image:: https://raw.github.com/amintos/akira/playground/model/images/connection_endpoints_7.png

In the end the connection knows its endpoints in both processes.


Questions?
----------

Where is it implemented? `(py)
<https://github.com/amintos/akira/blob/playground/process/setConnectionEndpointsAlgorithm.py>`_

How is a connection serialized? `(html)
<serialize_connections.html>`__
`(rst)
<serialize_connections.rst>`__

What is that Process object good for? `(html)
<process.html>`__
`(rst) 
<process.rst>`__









