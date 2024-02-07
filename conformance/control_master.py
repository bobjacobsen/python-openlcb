#!/usr/bin/env python3.10

'''
Top level of testing suite
'''

# We only import each specific option as it's 
# invoked to reduce startup time and propagation of errors
# during development

def prompt() :
    print("\nOpenLCB test program")
    print(" 0 Setup")
    print(" 1 Message Network testing")
    print(" 2 SNIP testing")
    print(" 3 Event Transport testing")
    print(" 4 Datagram Transport testing")
    print(" 5 Memory Configuration testing")
    print("  ")
    print(" q  Quit")
    
def main() :
    '''
    loop to test against SNIP Standard
    '''
    while True :
        prompt()
        selection = input(">> ")
        match selection :
            case "0" : 
                import control_setup
                control_setup.main()

            case "1" : 
                import control_message
                control_message.main()
           
            case "2" : 
                import control_snip
                control_snip.main()
                       
            case "3" : 
                import control_events
                control_events.main()
                       
            case "4" : 
                import control_datagram
                control_datagram.main()
                       
            case "5" : 
                import control_memory
                control_memory.main()
                       
            case "q" | "Q" : return
                   
            case _ : continue
            
    return
if __name__ == "__main__":
    main()
