#!/usr/bin/env python3.10

'''
Simple runner for Datagram suite
'''

import check_da30_dr

def prompt() :
    print("\nDatagram Transport Standard testing")
    print(" 0 Run all in sequence")
    print(" 1 Datagram Reception testing")
    print("  ")
    print(" q go back")

def testAll() :
    result = 0
 
    print("\nDatagram Reception testing")
    result += check_da30_dr.test()

    if result == 0 :
        print("\nSuccess - all passed")
    else:
        print("\nAt least one test failed")
        
    return result
    
def main() :
    '''
    loop to test against SNIP Standard
    '''
    while True :
        prompt()
        selection = input(">> ")
        match selection :
            case "1" : 
                print("\nDatagram Reception testing")
                check_da30_dr.test()
           
            case  "0" :
                testAll()
            
            case "q" | "Q" : return
            
            case _ : continue
                   
    return
if __name__ == "__main__":
    main()
