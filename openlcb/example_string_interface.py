# Example of raw socket communications over the physical connection, in this case a socket. 

# specify connection information
host = "192.168.16.212"
port = 12021

from tcpsocket import TcpSocket

s = TcpSocket()
s.connect(host, port)

#######################

# send a AME frame in GridConnect string format with arbitrary source alias to elicit response
AME = ":X10702001N;"
s.send(AME)
print ("SR: "+AME)

# display response - should be RID from node(s)
while True :  # have to kill this manually
    print("RR: "+s.receive())
    