from dataclasses import dataclass

@dataclass(frozen=True)
class DefenseConfig:
    name:str
    reinforced_prompt: bool = False
    sandwich: bool = False
    spotlighting: bool = False
    input_classifier: bool = False
    code_validation: bool = False


#D6 = D1 + D3 + D5
#D7 = D1 + D5
DEFENSES = {
    "D0": DefenseConfig("D0"),
    "D1": DefenseConfig("D1", reinforced_prompt=True, sandwich=True),
    "D2": DefenseConfig("D2", spotlighting=True),
    "D3": DefenseConfig("D3", input_classifier=True),
    "D5": DefenseConfig("D5", code_validation=True),
    "D6": DefenseConfig("D6", reinforced_prompt=True, sandwich=True, input_classifier=True, code_validation=True),
    "D7": DefenseConfig("D6", reinforced_prompt=True, sandwich=True, code_validation=True)
}