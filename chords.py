#!/usr/bin/python3

from collections import OrderedDict
CHORD_SHAPES = OrderedDict()
CHORD_SHAPES["min7"] = [
    [
        " o ",
        "o .",
        " x ",
    ],
    [
        " ox",
        "o .",
    ],
    [
        " o ",
        " ox",
        "  .",
    ],
    [
        "o .",
        "ox",
    ]

]
CHORD_SHAPES["maj7"] = [
    [
        " . o",
        "x o ",
    ],
    [
        "x  ",
        ". o",
        " o ",
    ],
    [
        "x o",
        ". o",
    ],
    [
        " . ",
        "x o",
        "  o",
    ]
]
CHORD_SHAPES["maj9"] = [
    [
        "  o",
        " . o",
        "x o ",
    ],
    [
        "xo ",
        ". o",
        " o ",
    ],
    [
        "xoo",
        ". o",
    ],
    [
        " . ",
        "xoo",
        "  o",
    ],
    [
        " . o",
        "xoo",
    ]
]

CHORD_SHAPES["maj7b5"] = [
    [
        "   o",
        "x oo",
    ],
    [
        " x",
        "   o",
        "  oo",
    ],
    [
        "x o",
        "  o",
        "  o",
    ],
    [
        "x oo",
        "  o",
    ]
]
CHORD_SHAPES["min7b5"] = [
    [
        " o ",
        "o",
        " x  o",
    ],
    [
        " ox",
        "o",
        "    o",
    ],
    [
        " ox  o",
        "o",
    ],
    [
        "o",
        "ox  o",
    ]
]
CHORD_SHAPES["6"] = [
    [
        " .o",
        "x o",
    ],
    [
        "x",
        ".o",
        " o",
    ],
    [
        "x o",
        ".o",
    ],
    [
        " .",
        "x o",
        " o",
    ]
]
CHORD_SHAPES["maj6"] = [
    [
        " .oo",
        "x o",
    ],
    [
        "x",
        ".oo",
        " o",
    ],
    [
        "x o",
        ".oo",
    ],
    [
        " .",
        "x o",
        " oo",
    ],
    [
        " .o",
        "x o",
        "  o",
    ]
]
CHORD_SHAPES["sus2"] = [
    [
        " o",
        "xo ",
    ]
]
CHORD_SHAPES["Q"] = [
    [
        "o",
        "o",
        "x",
    ]
]
CHORD_SHAPES["Qt"] = [
    [
        "  o",
        " o",
        "x",
    ]
]
CHORD_SHAPES["dim"] = [
    [
        "o",
        " o",
        "  x",
    ],
    [
        "o  x",
        " o",
    ],
    [
        "  x ",
        "o  o",
    ]
]
CHORD_SHAPES["aug"] = [
    [
        "x o o",
    ],
    [
        "x",
        "",
        " o o",
    ],
    [
        "x o",
        "",
        "   o",
    ]
]
CHORD_SHAPES["lyd"] = [
    [
        "x oo",
    ],
    [
        "x  ",
        "",
        " oo",
    ],
    [
        "x o",
        "",
        "  o",
    ]

]
CHORD_SHAPES["sus4"] = [[
    "oo",
    "x ",
]]
CHORD_SHAPES["sus4b5"] = [
    [
        "o.",
        "x  o",
    ],
    [
        " x",
        "o.",
        "   o",
    ],
    [
        " x   o",
        "o.",
    ],
    [
        "o",
        "x   o",
        ".",
    ]
]
CHORD_SHAPES["phryg"] = [
    [
        "o  .",
        "  x",
    ],
    [
        "   x",
        "o  .",
    ],
    [
        "o  ",
        "  x",
        "  .",
    ]
]
CHORD_SHAPES["loc"] = [
    [
        " o",
        "o",
        "  x",
    ],
    [
        " o x",
        "o",
    ],
    [
        "o",
        "o x",
    ]
]
CHORD_SHAPES["minmaj7"] = [
    [
        "o . o",
        " x",
    ],
    [
        "  x",
        "o . o",
    ],
    [
        "o",
        " x",
        " . o",
    ],
    [
        "o .",
        " x",
        "   o",
    ]
]
# 13th chords voiced with a 6th
CHORD_SHAPES["dom6"] = [
    [
        "o ",
        " .o",
        "x o",
    ],
    [
        "ox",
        " .o",
        "  o",
    ],
    [
        "ox o",
        " .o",
    ],
    [
        "  .",
        "ox o",
        "  o",
    ],
    [
        "  .o",
        "ox o",
    ]
]
CHORD_SHAPES["dom7"] = [
    [
        "o ",
        " .",
        "x o",
    ],
    [
        "ox",
        " .",
        "  o",
    ],
    [
        "ox o",
        " .",
    ],
    [
        "  .",
        "ox o",
    ]
]
CHORD_SHAPES["min6"] = [
    [
        "o oo",
        " x ",
    ],
    [
        "  x",
        "o oo",
    ],
    [
        " o",
        "  x",
        "  oo",
    ],
    [
        " o o",
        "  x",
        "   o",
    ]
]
CHORD_SHAPES["maj"] = [
    [
        " o",
        "x o",
    ],
    [
        " x",
        " o",
        "  o",
    ],
    [
        "x o",
        "o",
    ]
]
CHORD_SHAPES["min"] = [
    [
        "o o",
        " x ",
    ],
    [
        "  x",
        "o o",
    ],
    [
        " o",
        "  x",
        "  o",
    ]
]
