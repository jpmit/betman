# matchconst.py
# James Mithen
# jamesmithen@gmail.com
#
# mapping from BDAQ event names to BF event names. most of the event
# names are the same but some are different!
# note that the following BF events don't have BDAQ equivalents at the
# moment:
# Athletics
# Basketball
# Bowls
# Financial Bets
# Netball
# Poker
# Politics

# keys here are BDAQ event name, values are corresponding BF event
# name.
EVENTMAP = {'American Football'          : 'American Football',
            'Australian Rules'           : 'Australian Rules', 
            'Baseball'                   : 'Baseball',         
            'Boxing'                     : 'Boxing',           
            'Cricket'                    : 'Cricket',          
            'Cycling'                    : 'Cycling',          
            'Darts'                      : 'Darts',            
            'Formula 1'                  : 'Motor Sport',
            'GAA' 				           : 'Gaelic Games',
            'Golf'                       : 'Golf',             
            'Greyhound Racing'           : 'Greyhound Racing',
#            'Greyhound - Todays Card'    : 'Greyhound - Todays Card',
            'Horse Racing'               : 'Horse Racing',
#            'Horse Racing - Todays Card' : 'Horse Racing',
#            'Mixed Martial Arts'         : 'Mixed Martial Arts',
            'Rugby League'               : 'Rugby League',       
            'Rugby Union'                : 'Rugby Union',        
            'Soccer'                     : 'Soccer',
#            'Soccer - Fixtures'          : 'Soccer',
            'Special Bets'               : 'Special Bets',       
            'Tennis'                     : 'Tennis'             
}
