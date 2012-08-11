
.. |explanation| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_explanation.png
.. |local| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_local.png
.. |direct| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_direct.png
.. |indirect1| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_indirect_1.png
.. |indirect2| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_indirect_2.png
.. |indirect3| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_indirect_3.png
.. |indirect4| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_indirect_4.png
.. |indirect5| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_indirect_5.png
.. |classDiagram| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_class_diagram.png

LocalObjectDatabase
===================

A LocalObjectDatabase is a id-to-object storage.
Objects can be stored under multiple references and such under multiple ids.

There are three kinds of references present. 
Although they may reference the same object, those three types are used according to the process
the reference object is in and how it got there.

|classDiagram| 

All references have a attribute *process* representing the process of the referenced object.
Also they all have an *id* and the *database* they are stored in.
The *id*, the *process* and the *database* together identify an object.
The process is nescessairy because the database exists in every process.

See the following illustrations for how references are used.

|explanation|

Below LocalDatabaseReferences are used in the process where the referenced object is.

|local|

They have a *value* that can be set and got. This values is looked up and stored in the database under the id of the reference.
If the reference gets deleted the id "1" is popped from the database.

See what happens when an object crosses border to an other process:

|direct|

First the object is stored under the id "2" . Then a reference constructor is sent to the other process.
In the other process a RemoteReference is built that directly references the object under the id 2.
If the reference is deleted a call is made to the process that pops the id "2" from the database.

|indirect1|

When a direct reference is sent to another process it can not get a new id for the object. Sending must be fast.
Instead the direct reference is referenced by the IndirectRemoteDatabaseReference. 
This prevents the deletion of the object under id "2" in case the direct reference is deleted.

|indirect2|

When the indirect reference is created a call is sent to the original process to get a new direct reference. 

The old reference is freed:

|indirect3|







