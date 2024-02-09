#!/usr/bin/env python3.10

'''
Top level of checking suite
'''

# We only import each specific option as it's 
# invoked to reduce startup time and propagation of errors
# during development

def prompt() :
    print("\nOpenLCB checking program")
    print(" s Setup")
    print("")
    print(" 0 Frame Transport checking")
    print(" 1 Message Network checking")
    print(" 2 SNIP checking")
    print(" 3 Event Transport checking")
    print(" 4 Datagram Transport checking")
    print(" 5 Memory Configuration checking")
    print("  ")
    print(" q  Quit")
    
def main() :
    '''
    loop to check against SNIP Standard
    '''
    while True :
        prompt()
        selection = input(">> ")
        match selection :
            case "s" : 
                import control_setup
                control_setup.main()

            case "0" : 
                import control_frame
                control_frame.main()

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
