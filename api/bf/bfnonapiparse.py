import xml.etree.ElementTree as etree
from betman import const, Selection

def ParseSelections(mids, xmlstr):
    root = etree.fromstring(xmlstr)
    selections = []
    # check we have one eventnode per mid in list
    enodes = root[0][1][0][0]
    return root
    #assert len(mids) == len(enodes)
    for mnum, enode in enumerate(enodes):
        selections.append([])
        # get one eventnode per market queried        
        for runner in enode[1][0][3]:
            name = runner[0][1].text
            sid = runner[3].text
            # exchange tag - this contains prices
            ex = runner[1]
            bprices = [(p[0].text, p[1].text) for p in ex[0]]
            lprices = [(p[0].text, p[1].text) for p in ex[1]]
            # add the selection to the list
            # we can fill in the things currently None later on...
            selections[mnum].append(Selection(name, sid, mids[mnum], None,
                                              None, None, None, None,
                                              bprices, lprices,
                                              const.BFID))
    # selections is a list of lists, e.g. selections[0] is a list
    # whose elements are Selection objects for the market with id
    # mids[0].
    return selections
