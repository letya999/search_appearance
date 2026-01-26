from enum import Enum

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class AgeGroup(str, Enum):
    GROUP_18_24 = "18-24"
    GROUP_25_34 = "25-34"
    GROUP_35_44 = "35-44"
    GROUP_45_54 = "45-54"
    GROUP_55_PLUS = "55+"

class Ethnicity(str, Enum):
    CAUCASIAN = "caucasian"
    AFRICAN = "african" # Black
    ASIAN = "asian"
    LATINO = "latino" # Hispanic
    MIDDLE_EASTERN = "middle_eastern"
    INDIAN = "indian" # South Asian
    OTHER = "other"

class Height(str, Enum):
    SHORT = "short"     # < 160
    MEDIUM = "medium"   # 160-175
    TALL = "tall"       # 175-190
    VERY_TALL = "very_tall" # > 190

class BodyType(str, Enum):
    SLIM = "slim"
    ATHLETIC = "athletic"
    AVERAGE = "average"
    CURVY = "curvy"
    PLUS_SIZE = "plus_size"

class FaceShape(str, Enum):
    OVAL = "oval"
    ROUND = "round"
    SQUARE = "square"
    HEART = "heart"
    DIAMOND = "diamond"
    OBLONG = "oblong"

class EyeColor(str, Enum):
    BLUE = "blue"
    GREEN = "green"
    HAZEL = "hazel"
    BROWN = "brown"
    BLACK = "black" # Dark brown really
    GREY = "grey"

class EyeShape(str, Enum):
    ALMOND = "almond"
    ROUND = "round"
    MONOLID = "monolid"
    HOODED = "hooded"
    DOWNTURNED = "downturned"
    UPTURNED = "upturned"

class Nose(str, Enum):
    SMALL = "small"
    AVERAGE = "average"
    LARGE = "large"
    STRAIGHT = "straight"
    HOOKED = "hooked"
    BUTTON = "button"

class Lips(str, Enum):
    THIN = "thin"
    AVERAGE = "average"
    FULL = "full"

class Jawline(str, Enum):
    SOFT = "soft"
    DEFINED = "defined"
    STRONG = "strong"

class HairColor(str, Enum):
    BLACK = "black"
    DARK_BROWN = "dark_brown"
    LIGHT_BROWN = "light_brown"
    BLONDE = "blonde"
    RED = "red"
    GREY = "grey"
    DYED = "dyed" # Colorful

class HairLength(str, Enum):
    BALD = "bald"
    SHORT = "short"
    MEDIUM = "medium" # Shoulder
    LONG = "long"

class HairTexture(str, Enum):
    STRAIGHT = "straight"
    WAVY = "wavy"
    CURLY = "curly"
    COILY = "coily" # Afro

class FacialHair(str, Enum):
    NONE = "none"
    STUBBLE = "stubble"
    BEARD = "beard"
    MUSTACHE = "mustache"
    GOATEE = "goatee"

class SkinTone(str, Enum):
    FAIR = "fair"
    LIGHT = "light"
    MEDIUM = "medium"
    TAN = "tan"
    DARK = "dark"

class Glasses(str, Enum):
    NONE = "none"
    READING = "reading"
    SUNGLASSES = "sunglasses"

class Tattoos(str, Enum):
    NONE = "none"
    MINIMAL = "minimal" # Discrete
    VISIBLE = "visible" # Sleeves, etc.

class Style(str, Enum):
    CASUAL = "casual"
    FORMAL = "formal"
    CHIC = "chic"
    BOHEMIAN = "bohemian"
    STREETWEAR = "streetwear"
    VINTAGE = "vintage"
    EDGY = "edgy"
    SPORTY = "sporty"

class Vibe(str, Enum):
    FRIENDLY = "friendly"
    SERIOUS = "serious"
    CONFIDENT = "confident"
    SHY = "shy"
    ENERGETIC = "energetic"
    CALM = "calm"
    INTELLECTUAL = "intellectual"
