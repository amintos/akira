
How is a connection serialized?
-------------------------------

Connections from `Listener
<https://github.com/amintos/akira/blob/playground/process/Listener.py>`_ support the *with* statement.
Everytime a statement is executed with a connection, the connection is put on top of the stack of `TopConnection
<https://github.com/amintos/akira/blob/playground/process/TopConnection.py>`_
. 

.. image:: https://github.com/amintos/akira/raw/playground/documentation/images/connection_stack.png

This happens if a connection receives an object or sends an object.
Sending a serialized connection anywhere else than to it's other end point 
doesn't make sense - so the connection assures it is on top of that stack.
Because the connection is top of the stack when it is sent and received, 
during unpickling the other endpoint of the connection is the top of the stack. 
So the other endpoint is returned as unpickled connection.



