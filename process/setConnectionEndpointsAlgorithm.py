
def setConnectionEndpoints(aConnection):
    # this is called on the other side
    aConnection.call(connectToProcess, (Process.thisProcess, aConnection))

def connectToProcess(aProcessInOtherProcess, aConnection):
    # aProcessInOtherProcess is now a shadow
    if not getattr(aConnection, '_tag_setConnectionEndpointsWasHere', False):
        aConnection._tag_setConnectionEndpointsWasHere = True
        # connection already knows where it is connected to
        aConnection.toProcess(aProcessInOtherProcess)
        aConnection.call(connectToProcess, (Process.thisProcess, aConnection))
    aConnection.fromProcess(Process.thisProcess)
    aProcessInOtherProcess.addConnection(aConnection)
    Process.thisProcess.knowsProcess(aProcessInOtherProcess)
    
import Process
import TopConnection

