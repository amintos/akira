
How is a connection serialized?
-------------------------------

Connections from `Listener
<https://github.com/amintos/akira/blob/playground/process/Listener.py>`_ support the *with* statement.
Everytime a statement es executed with a connection, the connection is put on top of the stack of `TopConnection
<https://github.com/amintos/akira/blob/playground/process/TopConnection.py>`_
. This happens if a connection receives an object or sends an object.
If the connection gets pickled it assures that it is on top of this stack.
If it is, this implies that it is sent over itself. Because the connection is top of the stack when it is sent and received, during unpickling the top connection of the stack is the other side of the connection. So the other side is returned as unpickled connection.




