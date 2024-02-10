#!/usr/bin/env python3.10

'''
Simple runner for frame transport suite
'''

import check_fr10_init
import check_fr20_ame
import check_fr30_collide
import check_fr40_highbit

def prompt() :
    print("\nFrame Transport Standard checking")
    print(" 0 Run all in sequence")
    print(" 1 Initialization checking")
    print(" 2 AME checking")
    print(" 3 Collision checking")
    print(" 4 reserved bit checking")
    print("  ")
    print(" q go back")

def checkAll() :
    result = 0
 
    print("\nInitialization checking")
    result += check_fr10_init.check()

    print("\nAME checking")
    result += check_fr20_ame.check()

    print("\nCollision checking")
    result += check_fr30_collide.check()

    print("\nReserved bit checking")
    result += check_fr40_highbit.check()

    if result == 0 :
        print("\nSuccess - all passed")
    else:
        print("\nAt least one check failed")
        
    return result
    
def main() :
    '''
    loop to check against Frame Transport Standard
    '''
    while True :
        prompt()
        selection = input(">> ")
        match selection :
            case "1" : 
                print("\nInitialization checking")
                check_fr10_init.check()

            case "2" : 
                print("\nAME checking")
                check_fr20_ame.check()
           
            case "3" : 
                print("\nCollision checking")
                check_fr30_collide.check()
           
            case "4" : 
                print("\nReserved bit checking")
                check_fr40_highbit.check()
           
            case  "0" :
                checkAll()
            
            case "q" | "Q" : return
            
            case _ : continue
                   
    return
if __name__ == "__main__":
    main()
