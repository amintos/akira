
import Process
import TopConnection

def setConnectionEndpoints(aConnection):
    # this is called on the other side
    aConnection.call(connectToProcess, (Process.thisProcess, aConnection))

def connectToProcess(aProcessInOtherProcess, aConnection):
    # aProcessInOtherProcess is now a shadow
    aConnection.fromProcess(Process.thisProcess)
    if aConnection.toProcess().isProcess():
        # connection already knows where it is connected to
        return
    aConnection.toProcess(aProcessInOtherProcess)
    aProcessInOtherProcess.addConnection(aConnection)
    aConnection.call(connectToProcess, (Process.thisProcess, aConnection))
