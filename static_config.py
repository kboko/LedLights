
STATIC_CONFIG="""{
	"0xe4115b33e66fL": {
		"Name":"Dolu1",
		"Nodes": 
		[
			{ 	"name": "Koridor1",
			 	"button": { "pin" : 27 }
			}
		]
	},
	"0x74da388858b4L": {
		"Name":"UKoridor",
		"Nodes": 
		[
			{ 	"name": "Antre",
			 	"movement": {"pin" : 6 },
				"light": {"pin" : 23, "bright_thresh" : 10 }
			},
			{ 	"name": "KoridorDolu",
			 	"movement": {"pin" : 13},
				"light": {"pin" : 24, "bright_thresh" : 10 },
				"brightness": { "pin" : 17 }
			}
		]
	},
	"0x74da38548ee4L": {
		"Name":"UGore",
		"Nodes": 
		[
			{ 	"name": "KoridorGore",
			 	"movement": {"pin" : 5},
				"light": {"pin" : 24},
				"brightness": { "pin" : 27 }
			},
			{ 	"name": "Stylba",
			 	"movement": {"pin" : 6},
				"light": {"pin" : 25, "bright_thresh" : 10 },
				"brightness": { "pin" : 17 }
			},
			{ 	"name": "Bania",
			 	"movement": {"pin" : 22},
				"light": {"pin" : 23, "bright_thresh" : 10},
				"humidity": { "pin" : 13 },
				"brightness": { "pin" : 4 }
			}
		]
	},
	"0x74da388858a9L": {
		"Name":"UGarderob",
		"Nodes": 
		[
			{ 	"name": "Kenef",
			 	"movement": {"pin" : 6},
				"light": {"pin" : 23, "bright_thresh" : 10},
				"brightness": { "pin" : 4 },
				"button": { "pin" : 27 }
			},
			{ 	"name": "Garderob",
			 	"movement": {"pin" : 13},
				"light": {"pin" : 24, "bright_thresh" : 10},
				"brightness": { "pin" : 17 }
			}
		]
	}
}"""

"""
import json
j = json.loads(STATIC_CONFIG)
print j"""