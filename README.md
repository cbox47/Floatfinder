# Floatfinder
A python script which checks the steam market for specific CS2 skin listings, fetches their floats with an instance of CSFloat API hosted locally, and sends notifications to a telegram bot when a skin in the desired float range is found (if the skin's price is less than 15% more than the cheapest listing). Useful for finding low- or specific-float skins to be used in tradeup contracts at or close to market price.

**Warnings**: 
Automated price checking is somewhat allowed by Steam, but automated purchasing of items is disallowed by their TOS, would recommend against it. 

Steam will give 429 - too many requests for an undefined amount of time if the `SCAN_INTERVAL` is set too low

Information about the CSFloat Inspect API and how to self-host it can be found here: https://github.com/csfloat/inspect#how-to-install

Information about the Steam API endpoint used by the script can be found here: https://github.com/Revadike/InternalSteamWebAPI/wiki/Get-Market-Listing
