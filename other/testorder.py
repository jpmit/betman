import datetime

order = {
         '_SelectionId' : 17140160,
         # 1 is back, 2 is lay
         '_Stake': 0.5,
         '_Price': 10.0,
         '_Polarity' : 1,
         # this stuff comes from the market information
         '_ExpectedSelectionResetCount': 1,
         '_ExpectedWithdrawalSequenceNumber': 0,         
         '_CancelOnInRunning': True,
         '_CancelIfSelectionReset': True,
         # all of these are optional
         # _ExpiresAt:
         # _WithdrawalRepriceOption = ""
         # _KillType = ""
         # _FillOrKillThreshold = ""
         # _RestrictOrderToBroker = ""
         # _ChannelTypeInfo = ""
         # _PunterReferenceNumber = ""
}
