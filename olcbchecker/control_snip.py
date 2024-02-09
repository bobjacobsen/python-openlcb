#!/usr/bin/env python3.10

'''
Simple runner for SNIP suite
'''

import check_sn10_snip

def prompt() :
    print("\nSNIP Standard checking")
    print(" 0 Run all in sequence")
    print(" 1 SNIP reply checking")
    print("  ")
    print(" q go back")

def checkAll() :
    result = 0
 
    print("\nSNIP reply checking")
    result += check_sn10_snip.check()

    if result == 0 :
        print("\nSuccess - all passed")
    else:
        print("\nAt least one check failed")
        
    return result
    
def main() :
    '''
    loop to check against SNIP Standard
    '''
    while True :
        prompt()
        selection = input(">> ")
        match selection :
            case "1" : 
                print("\nSNIP reply checking")
                check_sn10_snip.check()
           
            case  "0" :
                checkAll()
            
            case "q" | "Q" : return
            
            case _ : continue
                   
    return
if __name__ == "__main__":
    main()
