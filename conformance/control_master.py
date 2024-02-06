#!/usr/bin/env python3.10

'''
Top level of testing suite
'''

import control_setup
import control_message
import control_snip
import control_events

def prompt() :
    print("\nOpenLCB test program")
    print(" 0 Setup")
    print(" 1 Message Network testing")
    print(" 2 SNIP testing")
    print(" 3 Event testing")
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
                control_setup.main()

            case "1" : 
                control_message.main()
           
            case "2" : 
                control_snip.main()
                       
            case "3" : 
                control_events.main()
                       
            case "q" | "Q" : return
                   
            case _ : continue
            
    return
if __name__ == "__main__":
    main()
