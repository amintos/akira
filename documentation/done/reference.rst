


.. |ReferenceProxyClass| image:: https://github.com/amintos/akira/raw/playground/documentation/images/ReferenceProxy_class.png
.. |ReferenceProxySync| image:: https://github.com/amintos/akira/raw/playground/documentation/images/ReferenceProxy_sync.png
.. |ReferenceProxyAsync| image:: https://github.com/amintos/akira/raw/playground/documentation/images/ReferenceProxy_async.png
.. |ReferenceProxyCallback| image:: https://github.com/amintos/akira/raw/playground/documentation/images/ReferenceProxy_callback.png
.. |ReferenceProxySend| image:: https://github.com/amintos/akira/raw/playground/documentation/images/ReferenceProxy_send.png

References 
----------

References of an object are implemented as proxies to an object.

|ReferenceProxyClass|

The method determines how the proxy communicates with the object referenced by the reference `(rst)
<LocalObjectDatabase.rst>`__ `(html)
<LocalObjectDatabase.html>`__.
Such an ReferenceProxy can be created by *reference.reference(object, method)*.
*method* is currently one of *sync()*, *async()*, *send()*, *callback()*

See the examples of communication below.

|ReferenceProxySync|

For synchronous communication: 
If a method call of whatever method is made to the ReferenceProxy it is redirected with all arguments to the object.
The call blocks until the object has successfully returned the result.
It is also possible to use *functools.partial* to set the timeout for the call or other arguments defined by *async()*

|ReferenceProxySend|

An other way of communicating is just sending calls to the object. 
Nothing blocks and no errors are returned.

|ReferenceProxyAsync|

Asynchronous communication is also possible and implemented by *async()*. 
When a method of the proxy is called, a Result object is returned. 
It has a *get()* method to get aValue of the original call to the object.
*get()* blocks until aValue arrives.

|ReferenceProxyCallback|

Callback communication is a way of communicating without waiting.
All method call sent to the proxy get a function *callback(aValue)* as first argument. 
The following arguments can be passed as usally.
If the call to the object succeeds without error the callback is called with the return value. 
Of cause one can use the *get()* method of result.

Questions?
----------

Where is it implemented? `(py)
<https://github.com/amintos/akira/blob/playground/process/reference.py>`__


Why does the *ReferenceProxy* has a *reference* attribute? `(rst)
<LocalObjectDatabase.rst>`__ `(html)
<LocalObjectDatabase.html>`__.
