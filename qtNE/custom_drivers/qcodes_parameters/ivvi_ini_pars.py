from custom_drivers.IVVI_gates import VirtualDAC

gate_map = {
'VSDe': (0,1,0.1),
'STR': (0,16,1),
'STL': (0,15,1),
'LBL': (0,3,1),
'RBL': (0,2,1),
'RBR': (0,12,1),
'LBR': (0,11,1),
'B1': (0,10,1),
'P1': (0,9,1),
'B2': (0,8,1),
'P2': (0,7,1),
'B3': (0,6,1),
'P3': (0,5,1),
'B4': (0,4,1),
'CT': (0,14,1),
'CB': (0,13,1)
}

ivvi_virtual = VirtualDAC('virtual_ivvi',[station.ivvi],gate_map)
station.add_component(ivvi_virtual)

for gate in gate_map:
    if gate in station.components:
        station.remove_component(gate)
        
    station.add_component(getattr(ivvi_virtual,gate))