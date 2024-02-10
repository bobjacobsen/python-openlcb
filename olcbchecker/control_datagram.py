#!/usr/bin/env python3.10

'''
Simple runner for Datagram suite
'''

import check_da30_dr

def prompt() :
    print("\nDatagram Transport Standard checking")
    print(" 0 Run all in sequence")
    print(" 1 Datagram Reception checking")
    print("  ")
    print(" q go back")

def checkAll() :
    result = 0
 
    print("\nDatagram Reception checking")
    result += check_da30_dr.check()

    if result == 0 :
        print("\nSuccess - all passed")
    else:
        print("\nAt least one check failed")
        
    return result
    
def main() :
    '''
    loop to check against Datagram Standard
    '''
    while True :
        prompt()
        selection = input(">> ")
        match selection :
            case "1" : 
                print("\nDatagram Reception checking")
                check_da30_dr.check()
           
            case  "0" :
                checkAll()
            
            case "q" | "Q" : return
            
            case _ : continue
                   
    return
if __name__ == "__main__":
    main()
