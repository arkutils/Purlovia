# Experimenting with

#%% Setup
from ue.properties import FloatProperty, IntProperty
from ue.proxy import *


#%% Proxy class
class DCSC(UEProxyStructure, uetype='/Script/ShooterGame.PrimalDinoStatusComponent'):
    MaxStatusValues = uefloats(100.0, 100.0, 0.0, 100.0, 0, '00000000')
    CanLevelUp = uebools(True, False, True, False)


#%% Tests
dcsc1 = DCSC()
dcsc2 = DCSC()

#%% Show 1
dcsc1.MaxStatusValues

#%% Show 2
dcsc2.MaxStatusValues

#%% Show
dcsc1.MaxStatusValues[0] = 'one'
dcsc2.MaxStatusValues[0] = 'two'
#%% Update
dcsc1.update({'MaxStatusValues': {0: FloatProperty.create(200)}})

#%% Show 1
dcsc1.MaxStatusValues

#%%
