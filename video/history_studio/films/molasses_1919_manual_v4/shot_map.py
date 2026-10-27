"""Individually storyboarded footage/narration pairs for Great Molasses Flood.
The narration comes from checked-in episode.json; boundaries are consciously
selected by story sentence, not random image matching or equal time slicing.
"""
# (number of consecutive original-script sentences, visual source type:key, exact visual intent)
MANUAL_SHOTS = [
[(2,'illustration:intro','Boston, January 15, 1919'),(3,'archive:tank','The storage tank before its failure'),(3,'graphic:rupture','What released the flood'),(3,'archive:panorama','The devastated neighborhood')],
[(1,'archive:panorama','A genuine 1919 photograph'),(1,'graphic:volume','2.3 million gallons'),(1,'graphic:victims','21 lives lost and about 150 injured'),(2,'archive:rail','The violent aftermath')],
[(1,'graphic:site','North End commercial waterfront'),(2,'archive:tank','Homes, industry and the elevated railway'),(1,'graphic:railway','Commercial Street railway context'),(2,'graphic:risk','Why a failure affected the neighborhood')],
[(1,'archive:tank','The 1915 storage tank'),(2,'graphic:dimensions','Fifty feet tall, roughly ninety feet across'),(1,'graphic:shipment','Molasses arrived by ship'),(2,'archive:tank','Tank and railway beside everyday workplaces')],
[(2,'graphic:molasses','Molasses was an industrial raw material'),(2,'graphic:process','Fermentation and distillation'),(1,'graphic:shipment','Ship to storage to distillery'),(2,'graphic:pressure','Hydrostatic pressure inside a full tank')],
[(1,'archive:tank','Visible tank leaks were reported'),(1,'graphic:leak','Molasses escaping through seams'),(2,'graphic:paint','Allegations of painting over the leaks'),(2,'graphic:warning','Concealment did not repair damage')],
[(2,'graphic:steel','Steel walls and structural seams'),(2,'graphic:rivets','Riveted plates under stress'),(1,'graphic:crack','How stressed joints can initiate cracking'),(2,'archive:rail','Evidence from the destroyed steelwork')],
[(2,'graphic:date','January 15, 1919'),(1,'graphic:weather','An unusually mild winter afternoon'),(1,'graphic:shipment','A recent shipment increased storage volume'),(2,'archive:tank','The tank under pressure')],
[(1,'graphic:pressure','Pressure rises with liquid depth'),(2,'graphic:crack','A seam or plate can lose strength'),(1,'graphic:rupture','The sudden structural failure'),(2,'archive:panorama','Damage after the rupture')],
[(1,'graphic:wave','The early rush of molasses'),(1,'graphic:speed','Reported initial speed was an estimate'),(1,'archive:panorama','Where the destructive liquid travelled'),(2,'archive:tracks','The wreckage it left behind')],
[(2,'archive:rail','Elevated railway damage'),(2,'archive:tracks','Buildings and rail structure'),(1,'archive:panorama','Crushed industrial waterfront'),(2,'graphic:rescue','An extraordinarily difficult rescue')],
[(1,'graphic:rescue','Rescuers had to move through sticky debris'),(2,'archive:tracks','The devastated rescue environment'),(2,'graphic:teams','Police, firefighters, sailors and Red Cross'),(2,'archive:panorama','The scale of the emergency')],
[(1,'graphic:victims','Twenty-one fatalities'),(2,'graphic:names','The people behind the casualty count'),(1,'graphic:firehouse','Firefighter George Layhe'),(2,'archive:loc','1919 original American Red Cross photograph')],
[(2,'archive:tracks','The wreckage around the railway'),(2,'archive:rail','Broken infrastructure'),(2,'archive:panorama','The damaged waterfront'),(2,'graphic:victims','A disaster, not a spectacle')],
[(1,'graphic:cleanup','The rescue became a long cleanup'),(1,'archive:tracks','Molasses and debris across the site'),(2,'graphic:saltwater','Harbor saltwater assisted cleanup'),(2,'archive:panorama','The destroyed North End')],
[(2,'archive:panorama','Investigators returned to the disaster site'),(1,'graphic:sabotage','The company blamed sabotage'),(1,'graphic:evidence','Claims require physical evidence'),(2,'graphic:steel','Evidence of structural weakness')],
[(2,'graphic:legal','Families sought accountability'),(1,'graphic:evidence','Tank design and testing under scrutiny'),(1,'graphic:judgment','1925 auditor report'),(2,'archive:panorama','The loss of life and property')],
[(2,'graphic:steel','Adequacy of the steel'),(2,'graphic:rivets','Riveted joints and pressure'),(2,'graphic:inspection','Professional oversight and inspection'),(2,'graphic:warning','Why known problems matter')],
[(2,'graphic:headlines','Newspapers reported the disaster'),(2,'graphic:victims','Early reports did not yet know the final toll'),(1,'archive:loc','1919 record of the aftermath'),(2,'graphic:warning','The risk of normalizing warning signs')],
[(2,'archive:panorama','Boston remembers the devastation'),(1,'graphic:volume','The danger was volume and weight'),(2,'graphic:wave','Heavy syrup moving at speed'),(2,'graphic:victims','A preventable industrial tragedy')],
[(3,'graphic:timeline','1915 construction to 1919 catastrophe'),(3,'graphic:leak','The warnings before the collapse'),(3,'graphic:judgment','The legal finding in 1925'),(3,'graphic:inspection','The safety lesson')],
[(1,'archive:panorama','The lasting historic evidence'),(2,'graphic:inspection','Sound engineering and timely inspection'),(2,'graphic:warning','Safety requires acting on problems'),(2,'graphic:outro','Facts Uncovered: Stories & Evidence')]
]
assert len(MANUAL_SHOTS)==22
assert sum(len(s) for s in MANUAL_SHOTS)==88
assert all(len(s)==4 for s in MANUAL_SHOTS)