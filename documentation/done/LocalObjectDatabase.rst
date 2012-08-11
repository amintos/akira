
.. |explanation| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_explanation.png
.. |local| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_local.png
.. |direct| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_direct.png
.. |indirect1| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_indirect_1.png
.. |indirect2| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_indirect_2.png
.. |indirect3| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_indirect_3.png
.. |indirect4| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_indirect_4.png
.. |indirect5| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_indirect_5.png
.. |classDiagram| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_class_diagram.png
.. |classDiagramLocal| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_class_diagram_local.png
.. |raceCondition| image:: https://raw.github.com/amintos/akira/playground/documentation/images/LocalObjectDatabase_reference_race.png

LocalObjectDatabase
===================

How references can be used
--------------------------

Objects can be stored in a LocalObjectDatabase with *localObjectDatabase.store(anObject)*.
This function returns a DatabaseReference to the object.
A simplified view of these objects can be seen below.

|classDiagramLocal|

All references have a *process* attribute. So one can send calls to the objects original process. 
Those calls may include such a DatabaseReference.
When deserialized in its orginal process, the reference object becomes a local one.
One can test on this with *isLocal()*.
Local references have a *value* attribute for the referenced object.
So one can access the object once one is in the objects process.

If you want to use reference proxies to objects see this: `(rst)
<reference.rst>`__ `(html)
<reference.html>`__



How references work
-------------------

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

If below a indirect reference is sent to another process, almost the same happens.

|indirect4|

The difference is the following: 
The new indirect reference references the direct "3" instead of the indirect "3".
Resulting in:

|indirect5|

Removed Race-condition
----------------------

Imagin the following scenario:

The indirect reference in the bottom was created in another process before the reference on the right received a new id.
As shown with the red arrow, it does reference the direct reference but the indirect one.

The race condition looks like this:

 1. The request for id 4 is sent.
 
 2. The request for id "3" is finished 
 
 3. The direct reference for "2" is deleted, not needed anymore.
 
 4. The object is popped from database under id "2"
 
 5. The request for a new id "4" arrives and tries to access the object under id "2" - an invalid operation.

|raceCondition|

But this race-condition is removed by referencing the direct references by indirect references.
So only if those indirect references receive a new id, the direct references are freed and really no longer required.


